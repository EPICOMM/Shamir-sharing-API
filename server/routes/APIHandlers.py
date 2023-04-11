import aiohttp
from aiohttp import web
import server.secret_sharing.__init__ as shamir_math_module
from server.models import RoomsManagers
import json


class APISecretCreationHandler:
    def __init__(self):
        self._rooms_manager = RoomsManagers.SecretCreationRoomsManager()

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
                                          'n': str(public_numbers.n),
                                          'e': str(public_numbers.e)
                                      }
                                  })

    async def get_secret_room(self, request):
        room_id = request.rel_url.query['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        public_numbers = room_stored_data.public_key.public_numbers()
        links_dict = {}
        for share in room_stored_data.participants_shares:
            if share.values is not None:
                links_dict[share.name] = f"/getSecretRoom/{room_id}/{share.name}"
            else:
                links_dict[share.name] = None
        return web.json_response({'links': links_dict,
                                  'public_key':
                                      {
                                          'n': str(public_numbers.n),
                                          'e': str(public_numbers.e)
                                      }
                                  })

    async def download_secret_share(self, request):
        room_id = request.match_info['room_id']
        user_id = request.match_info['user_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        popped_share = room_stored_data.pop_share_by_user(user_id)
        public_numbers = room_stored_data.public_key.public_numbers()
        file_fields = {
            "format_version": room_stored_data.format_version,
            "name": popped_share.name,
            "share_values": popped_share.values,
            'public_key':
                {
                    'n': str(public_numbers.n),
                    'e': str(public_numbers.e)
                },
            "formula": room_stored_data.formula
        }
        json_string = json.dumps(file_fields)
        json_bytes = str.encode(json_string)
        return web.Response(body=json_bytes, content_type="application/octet-stream")

    async def download_public_key(self, request):
        room_id = request.match_info['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        public_numbers = room_stored_data.public_key.public_numbers()
        file_fields = {
            'n': str(public_numbers.n),
            'e': str(public_numbers.e)
        }
        json_string = json.dumps(file_fields)
        json_bytes = str.encode(json_string)
        return web.Response(body=json_bytes, content_type="application/octet-stream")


class APIDocumentSigningHandler:
    def __init__(self):
        self._rooms_manager = RoomsManagers.DocumentSigningRoomsManager()

    async def create_signing_room(self, request):
        multipart = await request.multipart()
        pdf_binary = None
        pdf_name = "document.pdf"
        secret_part_binary = None
        while True:
            part = await multipart.next()
            if part is None:
                break
            if part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'application/pdf':
                pdf_binary = bytes(await part.read())
                if part.filename is not None:
                    pdf_name = part.filename
            elif part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'application/octet-stream':
                secret_part_binary = bytes(await part.read())

        json_string = secret_part_binary.decode()
        json_object = json.loads(json_string)
        room_id, creator_token = self._rooms_manager.create_room(json_object['name'], json_object['share_values'],
                                                                 int(json_object['public_key']['n']),
                                                                 int(json_object['public_key']['e'],
                                                                     json_object['formula']), pdf_binary, pdf_name,
                                                                 json_object['format_version'])
        return web.json_response({'room_id': room_id,
                                  'creator_token': creator_token
                                  })

    async def get_signing_room(self, request):
        room_id = request.rel_url.query['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        return web.json_response({
            'signed_count':len(room_stored_data.participants_shares),
            'participants_count': room_stored_data.participants_count,
            'enough_participants': room_stored_data.signing_available(),
            'original_document_link': f'/downloadOriginalDocument/{room_id}'
        })

    async def download_original_document(self, request):
        room_id = request.match_info['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        resp_headers = {'Content-Type': 'application/pdf',
                        'Content-Disposition': f'attachment; filename="{room_stored_data.pdf_name}"'}
        return web.Response(body=room_stored_data.pdf_binary, headers=resp_headers)

    async def sign_document(self, request):
        room_id = request.rel_url.query['room_id']
        share_binary = await request.read()
        json_string = share_binary.decode()
        json_object = json.loads(json_string)
        room = self._rooms_manager.get_room_stored_data(room_id)
        room.add_share(json_object['name'], json_object['share_values'])
        return web.Response(status=200)

    async def finish_signing(self, request):
        room_id = request.rel_url.query['room_id']
        creator_token = request.rel_url.query['creator_token']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        if room_stored_data.finish_signing(creator_token):
            return web.Response(status=400)
        resp_headers = {'Content-Type': 'application/pdf',
                        'Content-Disposition': f'attachment; filename="{room_stored_data.pdf_name}"'}
        return web.Response(body=room_stored_data.pdf_signed_binary, headers=resp_headers)

    async def download_signed_document(self, request):
        room_id = request.match_info['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        resp_headers = {'Content-Type': 'application/pdf',
                        'Content-Disposition': f'attachment; filename="{room_stored_data.pdf_name}"'}
        return web.Response(body=room_stored_data.pdf_signed_binary, headers=resp_headers)


SECRET_CREATION_HANDLER = APISecretCreationHandler()
DOCUMENT_SIGNING_HANDLER = APIDocumentSigningHandler()

ROUTES_LIST = [
    web.post('/createSecretRoom', SECRET_CREATION_HANDLER.create_secret_room),
    web.get('/getSecretRoom', SECRET_CREATION_HANDLER.get_secret_room),
    web.get('/downloadSecretShare/{room_id}/{user_id}', SECRET_CREATION_HANDLER.download_secret_share),
    web.get('/downloadPublicKey/{room_id}', SECRET_CREATION_HANDLER.download_public_key),
    web.post('/createSigningRoom', DOCUMENT_SIGNING_HANDLER.create_signing_room),
    web.post('/getSigningRoom', DOCUMENT_SIGNING_HANDLER.get_signing_room),
    web.get('/downloadOriginalDocument/{room_id}', DOCUMENT_SIGNING_HANDLER.download_original_document),
    web.post('/signDocument', DOCUMENT_SIGNING_HANDLER.sign_document),
    web.post('/finishSigning', DOCUMENT_SIGNING_HANDLER.finish_signing),
    web.post('/downloadSignedDocument/{room_id}', DOCUMENT_SIGNING_HANDLER.download_signed_document)
]
