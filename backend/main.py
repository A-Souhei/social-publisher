import os
from pathlib import Path

import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

DB_PATH = os.getenv("DB_PATH", "/data/schedule.db")
IMAGES_DIR = os.getenv("IMAGES_DIR", "/data/images")

app = FastAPI(title="Social Publisher Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

VALID_STATUSES = {"draft", "scheduled", "publishing", "published", "failed"}


def row_to_post(row: aiosqlite.Row) -> dict:
    platforms_raw = row["platforms"] or ""
    platforms = [p.strip() for p in platforms_raw.split(",") if p.strip()]
    text = row["text"] or ""
    image_path = row["image_path"]
    image_url = None
    if image_path:
        basename = Path(image_path).name
        image_url = f"/api/images/{basename}"
    return {
        "id": row["id"],
        "text": text,
        "text_preview": text[:140],
        "platforms": platforms,
        "image_path": image_path,
        "has_image": bool(image_path),
        "image_url": image_url,
        "scheduled_time": row["scheduled_time"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "published_at": row["published_at"],
        "error": row["error"],
    }


@app.get("/api/posts")
async def get_posts(status: str = "all"):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status and status != "all" and status in VALID_STATUSES:
            cursor = await db.execute(
                "SELECT * FROM posts WHERE status = ? ORDER BY COALESCE(scheduled_time, created_at) DESC",
                (status,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM posts ORDER BY COALESCE(scheduled_time, created_at) DESC"
            )
        rows = await cursor.fetchall()
    posts = [row_to_post(r) for r in rows]
    return {"posts": posts, "count": len(posts)}


@app.get("/api/posts/{post_id}")
async def get_post(post_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return row_to_post(row)


@app.get("/api/stats")
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT status, COUNT(*) as count FROM posts GROUP BY status"
        )
        rows = await cursor.fetchall()
    counts = {s: 0 for s in VALID_STATUSES}
    total = 0
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["count"]
        total += row["count"]
    counts["total"] = total
    return counts


@app.get("/api/images/{filename}")
async def get_image(filename: str):
    # Guard against path traversal — only allow bare basenames
    if "/" in filename or "\\" in filename or filename.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = Path(IMAGES_DIR) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(file_path))
