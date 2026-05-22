import os
from typing import Optional

import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = os.getenv("DB_PATH", "/data/schedule.db")

app = FastAPI(title="Community Manager Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_STATUSES = {"pending", "publishing", "published", "failed", "cancelled"}


def row_to_post(row: aiosqlite.Row) -> dict:
    targets_raw = row["targets"] or ""
    targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
    text = row["text"] or ""
    return {
        "id": row["id"],
        "text": text,
        "text_preview": text[:120],
        "targets": targets,
        "image_path": row["image_path"],
        "has_image": bool(row["image_path"]),
        "scheduled_time": row["scheduled_time"],
        "status": row["status"],
        "created_at": row["created_at"],
        "error": row["error"],
    }


@app.get("/api/posts")
async def get_posts(status: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status and status != "all" and status in VALID_STATUSES:
            cursor = await db.execute(
                "SELECT * FROM scheduled_posts WHERE status = ? ORDER BY scheduled_time ASC",
                (status,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM scheduled_posts ORDER BY scheduled_time ASC"
            )
        rows = await cursor.fetchall()
    return [row_to_post(r) for r in rows]


@app.delete("/api/posts/{post_id}")
async def cancel_post(post_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, status FROM scheduled_posts WHERE id = ?", (post_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Post not found")
        if row["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel post with status '{row['status']}'; only pending posts can be cancelled",
            )
        await db.execute(
            "UPDATE scheduled_posts SET status = 'cancelled' WHERE id = ?", (post_id,)
        )
        await db.commit()
    return {"id": post_id, "status": "cancelled"}


@app.get("/api/stats")
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT status, COUNT(*) as count FROM scheduled_posts GROUP BY status"
        )
        rows = await cursor.fetchall()
    counts = {s: 0 for s in VALID_STATUSES}
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["count"]
    return counts
