import json
import os
import re
import uuid
import base64
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from openai import OpenAI

from . import scheduler

IMAGES_DIR = Path.home() / ".hermes" / "plugins" / "social-publisher" / "images"
GPT_IMAGE_MODEL = "gpt-image-2"
# Cap quality at "medium" — "high"/"hd" is significantly more expensive.
QUALITY_ALIASES = {
    "standard": "medium",
    "hd": "medium",
    "high": "medium",
}

ALLOWED_PLATFORMS = {"linkedin_page", "facebook_page"}


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


def _facebook_pages() -> list[dict]:
    """Discover configured Facebook pages from numbered env vars.

    Scans for FACEBOOK_PAGE_<N>_NAME keys, reads the corresponding _ID and
    _TOKEN for each N, and returns only complete triples sorted by N.

    Numbered mode is opt-in: if any FACEBOOK_PAGE_<N>_(NAME|ID|TOKEN) var is
    present, only complete numbered triples are used and the legacy single-page
    vars are ignored (an incomplete triple yields an empty list rather than
    silently routing to the legacy page). The legacy single-page env vars
    (FACEBOOK_PAGE_ACCESS_TOKEN + FACEBOOK_PAGE_ID) are used only when no
    numbered vars are present at all.
    """
    name_pattern = re.compile(r"^FACEBOOK_PAGE_(\d+)_NAME$")
    numbered_key = re.compile(r"^FACEBOOK_PAGE_\d+_(NAME|ID|TOKEN)$")
    any_numbered = any(numbered_key.match(k) for k in os.environ)

    numbered: dict[int, dict] = {}
    for key, value in os.environ.items():
        m = name_pattern.match(key)
        if m:
            n = int(m.group(1))
            name = value.strip()
            page_id = os.getenv(f"FACEBOOK_PAGE_{n}_ID", "").strip()
            token = os.getenv(f"FACEBOOK_PAGE_{n}_TOKEN", "").strip()
            if name and page_id and token:
                numbered[n] = {"name": name, "id": page_id, "token": token}

    if numbered:
        return [numbered[n] for n in sorted(numbered)]

    # If the user opted into numbered mode (any FACEBOOK_PAGE_<N>_* key present) but
    # no complete triple exists, do NOT fall back to the legacy single page — that
    # would silently route to the wrong page on a typo/missing var. Report no pages.
    if any_numbered:
        return []

    # Legacy fallback: single page from FACEBOOK_PAGE_ACCESS_TOKEN + FACEBOOK_PAGE_ID,
    # only when no numbered vars are present at all.
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    page_id = os.getenv("FACEBOOK_PAGE_ID", "").strip()
    if token and page_id:
        name = os.getenv("FACEBOOK_PAGE_NAME", "default").strip() or "default"
        return [{"name": name, "id": page_id, "token": token}]

    return []


def _facebook_configured() -> bool:
    return bool(_facebook_pages())


def _resolve_facebook_page(name: str | None) -> dict:
    pages = _facebook_pages()
    if not pages:
        raise RuntimeError("No Facebook pages are configured")
    if name and name.strip():
        needle = name.strip().casefold()
        for page in pages:
            if page["name"].strip().casefold() == needle:
                return page
        raise RuntimeError(
            f"Unknown Facebook page '{name}'. Configured pages: {[p['name'] for p in pages]}"
        )
    if len(pages) == 1:
        return pages[0]
    raise RuntimeError(
        f"Multiple Facebook pages are configured; specify which one. "
        f"Available: {[p['name'] for p in pages]}"
    )


def _prepare_facebook_image(image_path: str) -> str:
    """Downscale and recompress an image so it stays well under Facebook's
    upload limits (Facebook recommends well below its 4 MB cap, and large PNGs
    are rejected/pixelated). Returns a path to a temporary JPEG; the caller is
    responsible for deleting it."""
    from PIL import Image

    MAX_DIM = 1440
    MAX_BYTES = 3_500_000
    with Image.open(image_path) as src:
        img = src.convert("RGB")
        img.thumbnail((MAX_DIM, MAX_DIM))  # preserves aspect ratio, only shrinks

    fd, tmp = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    quality = 85
    img.save(tmp, format="JPEG", quality=quality, optimize=True)
    while os.path.getsize(tmp) > MAX_BYTES and quality > 40:
        quality -= 15
        img.save(tmp, format="JPEG", quality=quality, optimize=True)
    return tmp


def _facebook_post(text: str, page_id: str, page_token: str, image_path: str | None = None):
    """Publish a post to a Facebook page."""
    if image_path:
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        prepared = _prepare_facebook_image(image_path)
        try:
            with open(prepared, "rb") as f:
                resp = requests.post(
                    url,
                    data={"caption": text, "access_token": page_token},
                    files={"source": f},
                    timeout=120,
                )
        finally:
            try:
                os.remove(prepared)
            except OSError:
                pass
    else:
        url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        resp = requests.post(
            url,
            data={"message": text, "access_token": page_token},
            timeout=30,
        )
    if not resp.ok:
        # Surface the Graph API error detail; raise_for_status() alone hides it.
        detail = resp.text
        try:
            err = resp.json().get("error", {})
            detail = (
                f"{err.get('message', '')} "
                f"(type={err.get('type')}, code={err.get('code')}, "
                f"subcode={err.get('error_subcode')}, fbtrace_id={err.get('fbtrace_id')})"
            )
        except Exception:
            pass
        raise RuntimeError(f"Facebook {resp.status_code} on {url}: {detail}")
    return resp.json()


def _do_publish(post_id: str) -> None:
    """
    Publish the Facebook target of a stored post.
    Called by the scheduler and publish_post tool.
    If FB is not configured or the post has no facebook_page target, does nothing.
    Updates post status on success or failure.
    """
    post = scheduler.get_post(post_id)
    if post is None:
        return

    if "facebook_page" not in post["platforms"]:
        return

    if not _facebook_configured():
        return

    now = datetime.now(timezone.utc).isoformat()
    try:
        page = _resolve_facebook_page(post.get("fb_page"))
        _facebook_post(post["text"], page["id"], page["token"], post.get("image_path"))
        scheduler.update_post(
            post_id,
            status="published",
            published_at=now,
            error=None,
        )
    except Exception as e:
        scheduler.update_post(post_id, status="failed", error=str(e))


# ---------------------------------------------------------------------------
# Image tools
# ---------------------------------------------------------------------------

def generate_image(params: dict, **kwargs) -> str:
    prompt = params["prompt"]
    size = params.get("size", "1024x1024")
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


def enhance_image(params: dict, **kwargs) -> str:
    image_path = params["image_path"]
    instruction = params["instruction"]
    size = params.get("size", "1024x1024")
    quality = _normalize_quality(params.get("quality"))
    try:
        _ensure_images_dir()
        from PIL import Image

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
# Post tool handlers
# ---------------------------------------------------------------------------

def list_facebook_pages(params: dict, **kwargs) -> str:
    pages = _facebook_pages()
    if not pages:
        return json.dumps({"pages": [], "count": 0, "note": "No Facebook pages configured"})
    return json.dumps({"pages": [p["name"] for p in pages], "count": len(pages)})


def create_post(params: dict, **kwargs) -> str:
    text = params.get("text", "").strip()
    platforms = params.get("platforms", [])
    image_path = params.get("image_path")
    scheduled_time = params.get("scheduled_time")
    facebook_page_param = params.get("facebook_page")

    try:
        if not text:
            return json.dumps({"error": "text is required"})
        if not isinstance(platforms, list) or not all(isinstance(p, str) for p in platforms):
            return json.dumps({"error": "platforms must be a list of strings, e.g. [\"linkedin_page\", \"facebook_page\"]"})
        invalid = [p for p in platforms if p not in ALLOWED_PLATFORMS]
        if invalid:
            return json.dumps({"error": f"Invalid platforms: {invalid}. Allowed: {sorted(ALLOWED_PLATFORMS)}"})
        if not platforms:
            return json.dumps({"error": "platforms must contain at least one entry"})

        fb_page = None
        notes = []
        if "facebook_page" in platforms:
            if _facebook_configured():
                try:
                    page = _resolve_facebook_page(facebook_page_param)
                    fb_page = page["name"]
                except RuntimeError as e:
                    return json.dumps({"error": str(e)})
            else:
                notes.append("Facebook credentials are not configured — this Facebook post is manual.")

        post = scheduler.create_post(text, platforms, image_path, scheduled_time, fb_page=fb_page)

        if "linkedin_page" in platforms:
            notes.append("LinkedIn posts are manual — copy the text from the dashboard and post manually.")
        if fb_page:
            notes.append(f"Facebook post targets page '{fb_page}' (auto-publishes).")

        result = dict(post)
        if notes:
            result["note"] = " ".join(notes)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def update_post(params: dict, **kwargs) -> str:
    post_id = params.get("post_id", "").strip()
    try:
        if not post_id:
            return json.dumps({"error": "post_id is required"})

        existing = scheduler.get_post(post_id)
        if existing is None:
            return json.dumps({"error": f"Post {post_id!r} not found"})

        fields = {}
        for key in ("text", "platforms", "image_path", "scheduled_time"):
            if key in params:
                fields[key] = params[key]

        if "platforms" in fields:
            platforms = fields["platforms"]
            if not isinstance(platforms, list) or not all(isinstance(p, str) for p in platforms):
                return json.dumps({"error": "platforms must be a list of strings, e.g. [\"linkedin_page\", \"facebook_page\"]"})
            if not platforms:
                return json.dumps({"error": "platforms must contain at least one entry"})
            invalid = [p for p in platforms if p not in ALLOWED_PLATFORMS]
            if invalid:
                return json.dumps({"error": f"Invalid platforms: {invalid}. Allowed: {sorted(ALLOWED_PLATFORMS)}"})

        # Resolve the Facebook page whenever the post will target facebook_page and
        # FB is configured — mirrors create_post so we never leave fb_page unset on a
        # FB-targeted post (which would fail at publish time).
        result_platforms = fields.get("platforms", existing.get("platforms", []))
        if "facebook_page" in result_platforms and _facebook_configured():
            if "facebook_page" in params:
                try:
                    fields["fb_page"] = _resolve_facebook_page(params["facebook_page"])["name"]
                except RuntimeError as e:
                    return json.dumps({"error": str(e)})
            elif not existing.get("fb_page"):
                # No name supplied and none stored: auto-select if unambiguous,
                # otherwise ask which page.
                try:
                    fields["fb_page"] = _resolve_facebook_page(None)["name"]
                except RuntimeError as e:
                    return json.dumps({"error": str(e)})
            # else: keep the page already stored on the post
        elif "facebook_page" in params and _facebook_configured():
            # Page name given even though FB isn't (yet) a target — resolve & store it.
            try:
                fields["fb_page"] = _resolve_facebook_page(params["facebook_page"])["name"]
            except RuntimeError as e:
                return json.dumps({"error": str(e)})

        updated = scheduler.update_post(post_id, **fields)
        if updated is None:
            return json.dumps({"error": f"Post {post_id!r} not found or is already published"})
        return json.dumps(updated)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


def publish_post(params: dict, **kwargs) -> str:
    post_id = params.get("post_id", "").strip()
    try:
        if not post_id:
            return json.dumps({"error": "post_id is required"})

        post = scheduler.get_post(post_id)
        if post is None:
            return json.dumps({"error": f"Post {post_id!r} not found"})

        if "facebook_page" not in post["platforms"]:
            return json.dumps({
                "note": "This post has no facebook_page target. Nothing to auto-publish — copy the text from the dashboard and post manually.",
                "post": post,
            })

        if not _facebook_configured():
            return json.dumps({
                "note": "Facebook credentials (FACEBOOK_PAGE_ACCESS_TOKEN / FACEBOOK_PAGE_ID) are not configured. This post is manual.",
                "post": post,
            })

        scheduler.update_post(post_id, status="publishing")
        _do_publish(post_id)
        result = scheduler.get_post(post_id)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_posts(params: dict, **kwargs) -> str:
    status = params.get("status")
    try:
        posts = scheduler.list_posts(status=status)
        return json.dumps({"posts": posts, "count": len(posts)})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_post(params: dict, **kwargs) -> str:
    post_id = params.get("post_id", "").strip()
    try:
        if not post_id:
            return json.dumps({"error": "post_id is required"})
        post = scheduler.get_post(post_id)
        if post is None:
            return json.dumps({"error": f"Post {post_id!r} not found"})
        return json.dumps(post)
    except Exception as e:
        return json.dumps({"error": str(e)})


def delete_post(params: dict, **kwargs) -> str:
    post_id = params.get("post_id", "").strip()
    try:
        if not post_id:
            return json.dumps({"error": "post_id is required"})
        deleted = scheduler.delete_post(post_id)
        if deleted:
            return json.dumps({"success": True, "message": f"Post {post_id} deleted."})
        return json.dumps({"success": False, "message": f"Post {post_id!r} not found."})
    except Exception as e:
        return json.dumps({"error": str(e)})
