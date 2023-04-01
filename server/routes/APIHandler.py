from aiohttp import web


class APIHandler:
    async def create_secret_room(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def get_secret_room(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def download_secret_share(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def create_signing_room(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def get_signing_room(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def download_original_document(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def sign_document(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def finish_signing(self, request):
        # code
        return web.json_response({'message': 'test'})

    async def download_signed_document(self, request):
        # code
        return web.json_response({'message': 'test'})


ROUTES_LIST = [
    web.post('/createSecretRoom', APIHandler.create_secret_room),
    web.post('/getSecretRoom', APIHandler.get_secret_room),
    web.post('/downloadSecretShare', APIHandler.download_secret_share),
    web.post('/createSigningRoom', APIHandler.create_signing_room),
    web.post('/getSigningRoom', APIHandler.get_signing_room),
    web.post('/downloadOriginalDocument', APIHandler.download_original_document),
    web.post('/signDocument', APIHandler.sign_document),
    web.post('/finishSigning', APIHandler.finish_signing),
    web.post('/downloadSignedDocument', APIHandler.download_signed_document)
]
