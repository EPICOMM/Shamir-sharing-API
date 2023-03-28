from aiohttp import web
from routes.endpoints import routes

server = web.Application()
server.add_routes(routes)

if __name__ == '__main__':
    web.run_app(server)
