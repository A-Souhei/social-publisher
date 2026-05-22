import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path.home() / ".hermes" / "plugins" / "social-publisher" / "schedule.db"

_lock = threading.Lock()
_stop_event = threading.Event()
_thread = None
_publish_fn = None


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                targets TEXT NOT NULL,
                image_path TEXT,
                scheduled_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                error TEXT
            )
        """)


def _to_utc(dt_str: str) -> datetime:
    """Parse ISO 8601 string, return UTC-aware datetime."""
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        raise ValueError(
            f"Invalid datetime format: {dt_str!r}. Use ISO 8601, e.g. '2025-01-15T14:30:00'"
        )
    # astimezone works for both naive (assumes local) and aware datetimes
    return dt.astimezone(timezone.utc)


def add_post(text: str, targets: list, image_path: str | None, scheduled_time: str) -> str:
    scheduled_dt = _to_utc(scheduled_time)
    if scheduled_dt <= datetime.now(timezone.utc):
        raise ValueError("scheduled_time must be in the future")
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with _lock, _get_conn() as conn:
        conn.execute(
            "INSERT INTO scheduled_posts(id, text, targets, image_path, scheduled_time, status, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (post_id, text, ",".join(targets), image_path, scheduled_dt.isoformat(), "pending", now),
        )
    return post_id


def list_posts() -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_posts WHERE status='pending' ORDER BY scheduled_time"
        ).fetchall()
    return [dict(r) for r in rows]


def cancel_post(post_id: str) -> bool:
    with _lock, _get_conn() as conn:
        cur = conn.execute(
            "UPDATE scheduled_posts SET status='cancelled' WHERE id=? AND status='pending'",
            (post_id,),
        )
        return cur.rowcount > 0


def _scheduler_loop():
    while not _stop_event.wait(30):
        try:
            now = datetime.now(timezone.utc).isoformat()
            with _lock, _get_conn() as conn:
                due = conn.execute(
                    "SELECT * FROM scheduled_posts WHERE status='pending' AND scheduled_time <= ?",
                    (now,),
                ).fetchall()
                for row in due:
                    conn.execute(
                        "UPDATE scheduled_posts SET status='publishing' WHERE id=?",
                        (row["id"],),
                    )

            for row in due:
                targets = [t for t in row["targets"].split(",") if t]
                try:
                    _publish_fn(row["text"], targets, row["image_path"] or None)
                    status, err = "published", None
                except Exception as e:
                    status, err = "failed", str(e)
                with _lock, _get_conn() as conn:
                    conn.execute(
                        "UPDATE scheduled_posts SET status=?, error=? WHERE id=?",
                        (status, err, row["id"]),
                    )
        except Exception:
            pass


def start_scheduler(publish_fn):
    global _thread, _publish_fn
    _publish_fn = publish_fn
    init_db()
    _stop_event.clear()
    _thread = threading.Thread(
        target=_scheduler_loop,
        daemon=True,
        name="social-publisher-scheduler",
    )
    _thread.start()


def stop_scheduler():
    _stop_event.set()
