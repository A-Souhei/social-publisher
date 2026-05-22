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
                "description": "Output image dimensions. Use auto when no exact aspect ratio is required."
            },
            "quality": {
                "type": "string",
                "enum": ["auto", "low", "medium", "standard", "hd"],
                "description": "Image quality is capped at medium. standard and hd map to medium for compatibility."
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
                "description": "Output image dimensions"
            },
            "quality": {
                "type": "string",
                "enum": ["auto", "low", "medium", "standard", "hd"],
                "description": "Image quality is capped at medium. standard and hd map to medium for compatibility."
            }
        },
        "required": ["image_path", "instruction"]
    }
}

PUBLISH_POST = {
    "name": "publish_post",
    "description": (
        "Publish a post immediately to one or more social media targets. "
        "Supported targets: linkedin_profile, linkedin_page, facebook_page. "
        "Can optionally include an image by providing a local file path."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The post text content"
            },
            "targets": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["linkedin_profile", "linkedin_page", "facebook_page"]
                },
                "description": "List of platforms/accounts to publish to",
                "minItems": 1
            },
            "image_path": {
                "type": "string",
                "description": "Optional: absolute local file path to an image to include in the post"
            }
        },
        "required": ["text", "targets"]
    }
}

SCHEDULE_POST = {
    "name": "schedule_post",
    "description": (
        "Schedule a post to be published at a specific future date and time. "
        "The post will be automatically published when the scheduled time arrives. "
        "Returns a schedule ID that can be used to cancel the post."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The post text content"
            },
            "targets": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["linkedin_profile", "linkedin_page", "facebook_page"]
                },
                "description": "List of platforms/accounts to publish to",
                "minItems": 1
            },
            "scheduled_time": {
                "type": "string",
                "description": "ISO 8601 datetime string for when to publish, e.g. '2025-01-15T14:30:00' or '2025-01-15T14:30:00+03:00'. If no timezone is given, local time is assumed."
            },
            "image_path": {
                "type": "string",
                "description": "Optional: absolute local file path to an image to include in the post"
            }
        },
        "required": ["text", "targets", "scheduled_time"]
    }
}

LIST_SCHEDULED_POSTS = {
    "name": "list_scheduled_posts",
    "description": "List all pending scheduled social media posts with their IDs, content preview, targets, and scheduled times.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}

CANCEL_SCHEDULED_POST = {
    "name": "cancel_scheduled_post",
    "description": "Cancel a scheduled post before it is published. Use the schedule ID returned by schedule_post or list_scheduled_posts.",
    "parameters": {
        "type": "object",
        "properties": {
            "schedule_id": {
                "type": "string",
                "description": "The schedule ID of the post to cancel"
            }
        },
        "required": ["schedule_id"]
    }
}
