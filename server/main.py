from aiohttp import web
from routes.APIHandler import ROUTES_LIST

server = web.Application()
server.add_routes(ROUTES_LIST)

if __name__ == '__main__':
    web.run_app(server)
