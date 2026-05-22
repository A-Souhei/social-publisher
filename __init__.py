from . import schemas, tools, scheduler


def register(ctx):
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
        name="create_post",
        toolset="social-publisher",
        schema=schemas.CREATE_POST,
        handler=tools.create_post,
    )
    ctx.register_tool(
        name="update_post",
        toolset="social-publisher",
        schema=schemas.UPDATE_POST,
        handler=tools.update_post,
    )
    ctx.register_tool(
        name="publish_post",
        toolset="social-publisher",
        schema=schemas.PUBLISH_POST,
        handler=tools.publish_post,
    )
    ctx.register_tool(
        name="list_posts",
        toolset="social-publisher",
        schema=schemas.LIST_POSTS,
        handler=tools.list_posts,
    )
    ctx.register_tool(
        name="get_post",
        toolset="social-publisher",
        schema=schemas.GET_POST,
        handler=tools.get_post,
    )
    ctx.register_tool(
        name="delete_post",
        toolset="social-publisher",
        schema=schemas.DELETE_POST,
        handler=tools.delete_post,
    )
