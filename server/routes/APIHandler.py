from aiohttp import web
import server.shamath.__init__ as shamir_math_module
from server.models import RSARoomsManager

class APIHandler:
    def __init__(self):
        self._rooms_manager = RSARoomsManager.RSARoomsManager()

    async def create_secret_room(self, request):
        data = await request.json()
        schema_type = data["type"]
        participants = data["names"]
        formula = None
        if schema_type == "threshold":
            threshold = int(data["threshold"])
            participants_string = ""
            for index, participant in enumerate(participants):
                participants_string += str(participant)
                if index != len(participants) - 1:
                    participants_string += ','
            formula = f"T{threshold}({participants_string})"
        elif schema_type == "formula":
            formula = data["formula"]
        room_id = self._rooms_manager.create_room(participants, formula)
        return web.json_response({'room_id': room_id}, status=200)

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


HANDLER = APIHandler()

ROUTES_LIST = [
    web.post('/createSecretRoom', HANDLER.create_secret_room),
    web.post('/getSecretRoom', HANDLER.get_secret_room),
    web.post('/downloadSecretShare/{room_id}', HANDLER.download_secret_share),
    web.post('/createSigningRoom', HANDLER.create_signing_room),
    web.post('/getSigningRoom', HANDLER.get_signing_room),
    web.post('/downloadOriginalDocument', HANDLER.download_original_document),
    web.post('/signDocument', HANDLER.sign_document),
    web.post('/finishSigning', HANDLER.finish_signing),
    web.post('/downloadSignedDocument', HANDLER.download_signed_document)
]
