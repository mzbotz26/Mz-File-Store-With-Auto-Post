from aiohttp import web

async def web_server():
    async def handler(request):
        return web.Response(text="Bot is running")

    app = web.Application()
    app.router.add_get("/", handler)
    return app
