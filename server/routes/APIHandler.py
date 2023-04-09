from aiohttp import web
import server.shamath.__init__ as shamir_math_module
from server.models import RSARoomsManager
import json
from io import BytesIO


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
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        public_numbers = room_stored_data.public_key.public_numbers()
        return web.json_response({'room_id': room_id,
                                  'public_key':
                                      {
                                          'n': public_numbers.n,
                                          'e': public_numbers.e
                                      }
                                  })

    async def get_secret_room(self, request):
        room_id = request.match_info['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        public_numbers = room_stored_data.public_key.public_numbers()
        links_dict = {}
        for share in room_stored_data.participants_shares:
            if share.values is not None:
                links_dict[share.name] = f"/{room_id}/{share.name}"
            else:
                links_dict[share.name] = None
        return web.json_response({'links': links_dict,
                                  'public_key':
                                      {
                                          'n': public_numbers.n,
                                          'e': public_numbers.e
                                      }
                                  })

    async def download_secret_share(self, request):
        room_id = request.match_info['room_id']
        user_id = request.match_info['user_id']
        popped_share = self._rooms_manager.pop_share_by_user(room_id, user_id)
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        public_numbers = room_stored_data.public_key.public_numbers()
        file_fields = {
            "format_version": room_stored_data.format_version,
            "name": popped_share.name,
            "share_values": popped_share.values,
            'public_key':
                {
                    'n': public_numbers.n,
                    'e': public_numbers.e
                },
            "formula": room_stored_data.formula
        }
        json_string = json.dumps(file_fields)
        json_bytes = str.encode(json_string)
        return web.Response(body=json_bytes, content_type="application/octet-stream")

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
    web.get('/getSecretRoom/{room_id}', HANDLER.get_secret_room),
    web.get('/downloadSecretShare/{room_id}/{user_id}', HANDLER.download_secret_share),
    web.post('/createSigningRoom', HANDLER.create_signing_room),
    web.post('/getSigningRoom', HANDLER.get_signing_room),
    web.post('/downloadOriginalDocument', HANDLER.download_original_document),
    web.post('/signDocument', HANDLER.sign_document),
    web.post('/finishSigning', HANDLER.finish_signing),
    web.post('/downloadSignedDocument', HANDLER.download_signed_document)
]
