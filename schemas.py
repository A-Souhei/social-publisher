GENERATE_IMAGE = {
    "name": "generate_image",
    "description": (
        "Generate an AI image from a text prompt using GPT Image. "
        "Returns a local file path to the generated PNG image. "
        "Use this when the user wants an AI-created image for their post."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Detailed description of the image to generate"
            },
            "size": {
                "type": "string",
                "enum": ["auto", "1024x1024", "1536x1024", "1024x1536", "1792x1024", "1024x1792"],
                "description": "Output image dimensions. Defaults to 1024x1024 (lowest cost) when omitted. Only request a larger size like 1536x1024 (landscape) or 1024x1536 (portrait) when the aspect ratio genuinely matters."
            },
            "quality": {
                "type": "string",
                "enum": ["auto", "low", "medium"],
                "description": "Image quality, capped at medium to control cost. Higher tiers (high/hd) are not available."
            }
        },
        "required": ["prompt"]
    }
}

ENHANCE_IMAGE = {
    "name": "enhance_image",
    "description": (
        "Enhance or modify an existing image using AI. "
        "Takes a local file path to an image and an instruction for how to change it. "
        "Returns a local file path to the enhanced PNG image. "
        "Use this when the user has uploaded or generated an image and wants to modify it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Absolute local file path to the source image (PNG, JPG, or WEBP)"
            },
            "instruction": {
                "type": "string",
                "description": "Natural language description of what changes to make to the image"
            },
            "size": {
                "type": "string",
                "enum": ["auto", "1024x1024", "1536x1024", "1024x1536", "1792x1024", "1024x1792"],
                "description": "Output image dimensions. Defaults to 1024x1024 (lowest cost) when omitted."
            },
            "quality": {
                "type": "string",
                "enum": ["auto", "low", "medium"],
                "description": "Image quality, capped at medium to control cost. Higher tiers (high/hd) are not available."
            }
        },
        "required": ["image_path", "instruction"]
    }
}

CREATE_POST = {
    "name": "create_post",
    "description": (
        "REQUIRED to save a post. Call this whenever the user asks to draft, write, create, compose, "
        "prepare, or schedule a social media post — 'drafting a post' ALWAYS means storing it with this "
        "tool, not just replying with the text. The post only appears in the review dashboard after this "
        "call; if you skip it, the work is lost. If you generated or enhanced an image for this post "
        "(e.g. with generate_image), pass the file path it returned as image_path. "
        "LinkedIn page posts are manual — the user copies the text from the dashboard and posts manually. "
        "LinkedIn personal posts auto-publish if LINKEDIN_ACCESS_TOKEN is configured; otherwise stored for manual reference. "
        "Facebook posts auto-publish (immediately or at the scheduled time) only if at least one Facebook "
        "page is configured; otherwise they are stored for manual reference. When more than one page is "
        "configured, set facebook_page to the target page's name (e.g. from 'post to <page>') — use "
        "list_facebook_pages to see the available names. "
        "Returns the stored post with its ID and status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The post text content"
            },
            "platforms": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["linkedin_page", "linkedin_personal", "facebook_page"]
                },
                "description": "Target platforms. linkedin_page = manual copy-paste; linkedin_personal = auto-publish if LINKEDIN_ACCESS_TOKEN is configured; facebook_page = auto-publish if FB is configured.",
                "minItems": 1
            },
            "image_path": {
                "type": "string",
                "description": (
                    "Optional: absolute local file path to an image to attach. If you just generated an "
                    "image with generate_image, pass the file_path it returned here so the image is stored "
                    "with the post and shown in the dashboard."
                )
            },
            "scheduled_time": {
                "type": "string",
                "description": (
                    "Optional ISO 8601 datetime for when to publish, e.g. '2025-06-01T14:30:00' or "
                    "'2025-06-01T14:30:00+03:00'. If omitted, post is saved as a draft. "
                    "Naive datetimes are treated as local time."
                )
            },
            "facebook_page": {
                "type": "string",
                "description": (
                    "Which Facebook page to post to, by name (e.g. 'Sahan\\'aina'). Required when "
                    "platforms includes facebook_page and more than one page is configured — if the "
                    "user says 'post to <page>', pass that name here. Use list_facebook_pages to see "
                    "the available names."
                )
            }
        },
        "required": ["text", "platforms"]
    }
}

UPDATE_POST = {
    "name": "update_post",
    "description": (
        "Modify a stored post's text, platforms, image, or schedule by ID. "
        "Use this to revise drafts ('change the wording', 'move it to Friday', 'add an image'). "
        "Cannot edit posts that are already published."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "ID of the post to update"
            },
            "text": {
                "type": "string",
                "description": "New post text"
            },
            "platforms": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["linkedin_page", "linkedin_personal", "facebook_page"]
                },
                "minItems": 1,
                "description": "Updated list of target platforms (at least one)"
            },
            "image_path": {
                "type": ["string", "null"],
                "description": "New image path, or null to remove the image"
            },
            "scheduled_time": {
                "type": ["string", "null"],
                "description": "New scheduled time (ISO 8601). Pass null to revert to draft."
            },
            "facebook_page": {
                "type": "string",
                "description": (
                    "Which Facebook page to post to, by name (e.g. 'Sahan\\'aina'). Required when "
                    "platforms includes facebook_page and more than one page is configured — if the "
                    "user says 'post to <page>', pass that name here. Use list_facebook_pages to see "
                    "the available names."
                )
            }
        },
        "required": ["post_id"]
    }
}

LIST_FACEBOOK_PAGES = {
    "name": "list_facebook_pages",
    "description": "List the configured Facebook pages you can publish to (by name).",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}

PUBLISH_POST = {
    "name": "publish_post",
    "description": (
        "Immediately publish a stored post's Facebook target now. "
        "Requires Facebook credentials (FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID) to be configured. "
        "If the post has no facebook_page target or FB is not configured, this returns a clear note — "
        "the post is manual and no status change is made."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "ID of the post to publish"
            }
        },
        "required": ["post_id"]
    }
}

LIST_POSTS = {
    "name": "list_posts",
    "description": (
        "List stored posts with full metadata. "
        "Optionally filter by status: draft, scheduled, publishing, published, or failed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["draft", "scheduled", "publishing", "published", "failed"],
                "description": "Optional status filter. Omit to list all posts."
            }
        }
    }
}

GET_POST = {
    "name": "get_post",
    "description": "Fetch a single stored post by ID with all metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "ID of the post to retrieve"
            }
        },
        "required": ["post_id"]
    }
}

DELETE_POST = {
    "name": "delete_post",
    "description": "Delete a stored post by ID. This permanently removes the post record.",
    "parameters": {
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "ID of the post to delete"
            }
        },
        "required": ["post_id"]
    }
}
