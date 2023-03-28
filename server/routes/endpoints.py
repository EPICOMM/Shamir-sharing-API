from aiohttp import web

routes = web.RouteTableDef()

@routes.post('/createSecretRoom')
async def create_secret_room(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/getSecretRoom')
async def get_secret_room(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/downloadSecretShare')
async def download_secret_share(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/createSigningRoom')
async def create_signing_room(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/getSigningRoom')
async def get_signing_room(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/downloadOriginalDocument')
async def download_original_document(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/signDocument')
async def sign_document(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/finishSigning')
async def finish_signing(request):
    # code
    return web.json_response({'message': 'test'})

@routes.post('/dlSignedDoc')
async def download_signed_document(request):
    # code
    return web.json_response({'message': 'test'})

