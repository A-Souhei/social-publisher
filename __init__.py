import os
from . import schemas, tools, scheduler


def register(ctx):
    # Start the background scheduler, wiring it to the core publish function
    scheduler.start_scheduler(tools._do_publish)

    ctx.register_tool(
        name="generate_image",
        toolset="social-publisher",
        schema=schemas.GENERATE_IMAGE,
        handler=tools.generate_image,
    )
    ctx.register_tool(
        name="enhance_image",
        toolset="social-publisher",
        schema=schemas.ENHANCE_IMAGE,
        handler=tools.enhance_image,
    )
    ctx.register_tool(
        name="publish_post",
        toolset="social-publisher",
        schema=schemas.PUBLISH_POST,
        handler=tools.publish_post,
    )
    ctx.register_tool(
        name="schedule_post",
        toolset="social-publisher",
        schema=schemas.SCHEDULE_POST,
        handler=tools.schedule_post,
    )
    ctx.register_tool(
        name="list_scheduled_posts",
        toolset="social-publisher",
        schema=schemas.LIST_SCHEDULED_POSTS,
        handler=tools.list_scheduled_posts,
    )
    ctx.register_tool(
        name="cancel_scheduled_post",
        toolset="social-publisher",
        schema=schemas.CANCEL_SCHEDULED_POST,
        handler=tools.cancel_scheduled_post,
    )
