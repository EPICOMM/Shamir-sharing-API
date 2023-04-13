from aiohttp import web
import aiohttp_cors
from aiohttp_catcher import Catcher, catch
from routes.APIHandlers import ROUTES_LIST
import asyncio


async def main():
    catcher = Catcher()

    await catcher.add_scenario(
        catch(Exception).with_status_code(400).with_additional_fields(
            {'type': 'ERROR', 'description': 'Something occured'}).and_return(None)
    )
    server_app = web.Application(middlewares=[catcher.middleware])
    server_app.add_routes(ROUTES_LIST)
    cors = aiohttp_cors.setup(server_app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })

    for route in list(server_app.router.routes()):
        cors.add(route)

    return server_app


if __name__ == '__main__':
    server = asyncio.run(main())
    web.run_app(server)
