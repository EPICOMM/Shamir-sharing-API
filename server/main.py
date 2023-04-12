from aiohttp import web
import aiohttp_cors
from routes.APIHandlers import ROUTES_LIST

server = web.Application()
server.add_routes(ROUTES_LIST)
cors = aiohttp_cors.setup(server, defaults={
   "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
  })

for route in list(server.router.routes()):
    cors.add(route)

if __name__ == '__main__':
    web.run_app(server)
