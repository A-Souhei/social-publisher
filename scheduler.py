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


def _row_to_dict(row) -> dict:
    d = dict(row)
    if "platforms" in d and d["platforms"]:
        d["platforms"] = [p.strip() for p in d["platforms"].split(",") if p.strip()]
    else:
        d["platforms"] = []
    return d


def _to_utc(dt_str: str) -> datetime:
    """Parse ISO 8601 string, return UTC-aware datetime."""
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        raise ValueError(
            f"Invalid datetime format: {dt_str!r}. Use ISO 8601, e.g. '2025-01-15T14:30:00'"
        )
    return dt.astimezone(timezone.utc)


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                platforms TEXT NOT NULL,
                image_path TEXT,
                scheduled_time TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                published_at TEXT,
                error TEXT
            )
        """)
        # Migrate: add fb_page column if not present
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(posts)").fetchall()}
        if "fb_page" not in cols:
            conn.execute("ALTER TABLE posts ADD COLUMN fb_page TEXT")


def create_post(
    text: str,
    platforms: list,
    image_path: str | None,
    scheduled_time: str | None,
    fb_page: str | None = None,
) -> dict:
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    scheduled_utc = None
    if scheduled_time:
        scheduled_utc = _to_utc(scheduled_time).isoformat()
    status = "scheduled" if scheduled_utc else "draft"
    with _lock, _get_conn() as conn:
        conn.execute(
            "INSERT INTO posts(id, text, platforms, image_path, scheduled_time, status, created_at, fb_page) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (post_id, text, ",".join(platforms), image_path, scheduled_utc, status, now, fb_page),
        )
    return get_post(post_id)


def update_post(post_id: str, **fields) -> dict | None:
    existing = get_post(post_id)
    if existing is None:
        return None
    if existing["status"] == "published":
        raise ValueError(f"Cannot edit post {post_id}: already published")

    now = datetime.now(timezone.utc).isoformat()
    allowed = {"text", "platforms", "image_path", "scheduled_time", "status", "published_at", "error", "fb_page"}
    updates = {k: v for k, v in fields.items() if k in allowed}

    # Coerce platforms list to CSV
    if "platforms" in updates and isinstance(updates["platforms"], list):
        updates["platforms"] = ",".join(updates["platforms"])

    # Coerce scheduled_time to UTC ISO
    if "scheduled_time" in updates and updates["scheduled_time"] is not None:
        updates["scheduled_time"] = _to_utc(updates["scheduled_time"]).isoformat()

    # Recompute status from scheduled_time unless status is explicitly passed
    if "scheduled_time" in updates and "status" not in updates:
        updates["status"] = "scheduled" if updates["scheduled_time"] else "draft"

    updates["updated_at"] = now

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [post_id]
    with _lock, _get_conn() as conn:
        conn.execute(f"UPDATE posts SET {set_clause} WHERE id = ?", values)
    return get_post(post_id)


def get_post(post_id: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def list_posts(status: str | None = None) -> list:
    with _get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM posts WHERE status = ? ORDER BY COALESCE(scheduled_time, created_at) DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM posts ORDER BY COALESCE(scheduled_time, created_at) DESC"
            ).fetchall()
    return [_row_to_dict(r) for r in rows]


def delete_post(post_id: str) -> bool:
    with _lock, _get_conn() as conn:
        cur = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        return cur.rowcount > 0


def _scheduler_loop():
    while not _stop_event.wait(30):
        try:
            now = datetime.now(timezone.utc).isoformat()
            with _lock, _get_conn() as conn:
                due = conn.execute(
                    "SELECT * FROM posts WHERE status = 'scheduled' AND scheduled_time <= ? AND platforms LIKE '%facebook_page%'",
                    (now,),
                ).fetchall()
                for row in due:
                    conn.execute(
                        "UPDATE posts SET status = 'publishing', updated_at = ? WHERE id = ?",
                        (now, row["id"]),
                    )

            for row in due:
                post_id = row["id"]
                try:
                    _publish_fn(post_id)
                except Exception:
                    pass
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
