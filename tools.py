import json
import os
import uuid
import base64
from datetime import datetime, timezone
from pathlib import Path

import requests
from openai import OpenAI

from . import scheduler

IMAGES_DIR = Path.home() / ".hermes" / "plugins" / "social-publisher" / "images"
GPT_IMAGE_MODEL = "gpt-image-2"
QUALITY_ALIASES = {
    "standard": "medium",
    "hd": "medium",
    "high": "medium",
}


def _ensure_images_dir():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def _normalize_quality(quality: str | None) -> str:
    if not quality:
        return "auto"
    return QUALITY_ALIASES.get(quality, quality)


def _image_response_bytes(response) -> bytes:
    image = response.data[0]
    image_base64 = getattr(image, "b64_json", None)
    if image_base64:
        return base64.b64decode(image_base64)

    image_url = getattr(image, "url", None)
    if image_url:
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        return img_response.content

    raise RuntimeError("OpenAI image response did not include image data")


# ---------------------------------------------------------------------------
# Image tools
# ---------------------------------------------------------------------------

def generate_image(params: dict) -> str:
    prompt = params["prompt"]
    size = params.get("size", "auto")
    quality = _normalize_quality(params.get("quality"))
    try:
        _ensure_images_dir()
        client = _openai_client()
        response = client.images.generate(
            model=GPT_IMAGE_MODEL,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        file_path = IMAGES_DIR / f"{uuid.uuid4()}.png"
        file_path.write_bytes(_image_response_bytes(response))
        return json.dumps({"file_path": str(file_path), "prompt": prompt})
    except Exception as e:
        return json.dumps({"error": str(e)})


def enhance_image(params: dict) -> str:
    image_path = params["image_path"]
    instruction = params["instruction"]
    size = params.get("size", "auto")
    quality = _normalize_quality(params.get("quality"))
    try:
        _ensure_images_dir()
        from PIL import Image
        import tempfile

        client = _openai_client()
        with Image.open(image_path) as img, tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            rgba_img = img.convert("RGBA")
            rgba_img.save(image_file, format="PNG")
            image_file.seek(0)

            response = client.images.edit(
                model=GPT_IMAGE_MODEL,
                image=image_file,
                prompt=instruction,
                n=1,
                size=size,
                quality=quality,
            )
        out_path = IMAGES_DIR / f"{uuid.uuid4()}_enhanced.png"
        out_path.write_bytes(_image_response_bytes(response))
        return json.dumps({"file_path": str(out_path), "original_path": image_path})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# LinkedIn helpers
# ---------------------------------------------------------------------------

def _linkedin_upload_image(image_path: str, author_urn: str, access_token: str) -> str:
    """Upload an image to LinkedIn and return its asset URN."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    register_body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    reg_resp = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        json=register_body,
        headers=headers,
        timeout=30,
    )
    reg_resp.raise_for_status()
    reg_data = reg_resp.json()
    upload_url = reg_data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = reg_data["value"]["asset"]

    with open(image_path, "rb") as f:
        upload_resp = requests.put(
            upload_url,
            data=f,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=120,
        )
    upload_resp.raise_for_status()
    return asset_urn


def _linkedin_post(text: str, author_urn: str, access_token: str, asset_urn: str | None = None):
    """Create a LinkedIn UGC post."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    share_content: dict = {
        "shareCommentary": {"text": text},
    }
    if asset_urn:
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [
            {
                "status": "READY",
                "media": asset_urn,
            }
        ]
    else:
        share_content["shareMediaCategory"] = "NONE"

    body = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": share_content
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    resp = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        json=body,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Facebook helpers
# ---------------------------------------------------------------------------

def _facebook_post(text: str, page_id: str, page_token: str, image_path: str | None = None):
    """Publish a post to a Facebook page."""
    if image_path:
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        with open(image_path, "rb") as f:
            resp = requests.post(
                url,
                data={"caption": text, "access_token": page_token},
                files={"source": f},
                timeout=120,
            )
    else:
        url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        resp = requests.post(
            url,
            json={"message": text, "access_token": page_token},
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Core publish logic (used by both handler and scheduler)
# ---------------------------------------------------------------------------

def _do_publish(text: str, targets: list, image_path: str | None) -> dict:
    """
    Publish to all targets. Raises on the first unrecoverable error.
    Returns a dict mapping target -> result.
    """
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    linkedin_page_urn = os.getenv("LINKEDIN_PAGE_URN")
    fb_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    fb_page_id = os.getenv("FACEBOOK_PAGE_ID")

    results = {}

    for target in targets:
        try:
            if target == "linkedin_page":
                if not linkedin_token:
                    raise RuntimeError("LINKEDIN_ACCESS_TOKEN not set")
                if not linkedin_page_urn:
                    raise RuntimeError("LINKEDIN_PAGE_URN not set")
                asset_urn = None
                if image_path:
                    asset_urn = _linkedin_upload_image(image_path, linkedin_page_urn, linkedin_token)
                resp = _linkedin_post(text, linkedin_page_urn, linkedin_token, asset_urn)
                results[target] = {"status": "published", "response": resp}

            elif target == "facebook_page":
                if not fb_token:
                    raise RuntimeError("FACEBOOK_PAGE_ACCESS_TOKEN not set")
                if not fb_page_id:
                    raise RuntimeError("FACEBOOK_PAGE_ID not set")
                resp = _facebook_post(text, fb_page_id, fb_token, image_path)
                results[target] = {"status": "published", "response": resp}

            else:
                results[target] = {"status": "error", "error": f"Unknown target: {target}"}

        except Exception as e:
            results[target] = {"status": "error", "error": str(e)}

    return results


# ---------------------------------------------------------------------------
# Tool handlers (return JSON strings)
# ---------------------------------------------------------------------------

def publish_post(params: dict) -> str:
    text = params["text"]
    targets = params["targets"]
    image_path = params.get("image_path")
    try:
        results = _do_publish(text, targets, image_path)
        return json.dumps({"results": results})
    except Exception as e:
        return json.dumps({"error": str(e)})


def schedule_post(params: dict) -> str:
    text = params["text"]
    targets = params["targets"]
    scheduled_time = params["scheduled_time"]
    image_path = params.get("image_path")
    try:
        post_id = scheduler.add_post(text, targets, image_path, scheduled_time)
        return json.dumps({
            "schedule_id": post_id,
            "message": f"Post scheduled successfully. ID: {post_id}",
            "targets": targets,
            "scheduled_time": scheduled_time,
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_scheduled_posts(params: dict) -> str:
    try:
        posts = scheduler.list_posts()
        formatted = []
        for p in posts:
            # Convert UTC stored time to local for display
            try:
                utc_dt = datetime.fromisoformat(p["scheduled_time"])
                local_dt = utc_dt.astimezone()
                human_time = local_dt.strftime("%Y-%m-%d %H:%M %Z")
            except Exception:
                human_time = p["scheduled_time"]

            formatted.append({
                "id": p["id"],
                "text_preview": p["text"][:100] + ("..." if len(p["text"]) > 100 else ""),
                "targets": [t for t in p["targets"].split(",") if t],
                "scheduled_time": human_time,
                "has_image": bool(p.get("image_path")),
            })
        return json.dumps({"scheduled_posts": formatted, "count": len(formatted)})
    except Exception as e:
        return json.dumps({"error": str(e)})


def cancel_scheduled_post(params: dict) -> str:
    schedule_id = params["schedule_id"]
    try:
        cancelled = scheduler.cancel_post(schedule_id)
        if cancelled:
            return json.dumps({"success": True, "message": f"Post {schedule_id} has been cancelled."})
        else:
            return json.dumps({
                "success": False,
                "message": f"No pending post found with ID {schedule_id}. It may have already been published, cancelled, or does not exist.",
            })
    except Exception as e:
        return json.dumps({"error": str(e)})
