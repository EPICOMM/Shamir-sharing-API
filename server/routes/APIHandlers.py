import aiohttp
from aiohttp import web
from server.models import RoomsManagers
from server.utils import utils
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
                links_dict[share.name] = f"/downloadSecretShare/{room_id}/{share.name}"
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
            "name": user_id,
            "share_values": popped_share,
            'public_key':
                {
                    'n': str(public_numbers.n),
                    'e': str(public_numbers.e)
                },
            "formula": room_stored_data.formula
        }
        json_string = json.dumps(file_fields)
        json_bytes = str.encode(json_string)
        resp_headers = {'Content-Type': 'application/octet-stream',
                        'Content-Disposition': f'attachment; filename="{room_stored_data.identifier}.sss"'}
        return web.Response(body=json_bytes, headers=resp_headers)

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
        resp_headers = {'Content-Type': 'application/octet-stream',
                        'Content-Disposition': f'attachment; filename="{room_stored_data.identifier}.rpk"'}
        return web.Response(body=json_bytes, headers=resp_headers)


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
                                                                 int(json_object['public_key']['e']),
                                                                 json_object['formula'], pdf_binary, pdf_name,
                                                                 json_object['format_version'])
        return web.json_response({'room_id': room_id,
                                  'creator_token': creator_token
                                  })

    async def get_signing_room(self, request):
        room_id = request.rel_url.query['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        return web.json_response({
            'signed_count': len(room_stored_data.participants_shares),
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
        return web.Response(body=room_stored_data.signed_pdf_binary, headers=resp_headers)

    async def download_signed_document(self, request):
        room_id = request.match_info['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        resp_headers = {'Content-Type': 'application/pdf',
                        'Content-Disposition': f'attachment; filename="{room_stored_data.pdf_name}"'}
        return web.Response(body=room_stored_data.signed_pdf_binary, headers=resp_headers)


class APISecretReissueHandler:
    def __init__(self):
        self._rooms_manager = RoomsManagers.SecretReissueRoomsManager()

    async def create_secret_reissue_room(self, request):
        formula = request.rel_url.query['formula']
        share_binary = await request.read()
        json_string = share_binary.decode()
        json_object = json.loads(json_string)
        room_id = self._rooms_manager.create_room(json_object['name'], json_object['share_values'],
                                                  int(json_object['public_key']['n']),
                                                  int(json_object['public_key']['e']),
                                                  json_object['formula'],
                                                  formula, json_object['format_version'])
        return web.Response(text=room_id)

    async def get_secret_reissue_room(self, request):
        room_id = request.rel_url.query['room_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        room_status = 'waiting_participants'
        links_dict = None
        if room_stored_data.participants_new_shares is not None:
            room_status = "reissued"
            links_dict = {}
            for share in room_stored_data.participants_shares:
                if share.values is not None:
                    links_dict[share.name] = f"/downloadReissuedSecretShare/{room_id}/{share.name}"
                else:
                    links_dict[share.name] = None
        return web.json_response({
            'signed_count': len(room_stored_data.participants_shares),
            'participants_count': room_stored_data.participants_count,
            'room_status': room_status,
            'links': links_dict
        })

    async def approve_secret_reissue(self, request):
        room_id = request.rel_url.query['room_id']
        share_binary = await request.read()
        json_string = share_binary.decode()
        json_object = json.loads(json_string)
        room = self._rooms_manager.get_room_stored_data(room_id)
        room.add_share(json_object['name'], json_object['share_values'])
        room.try_reissue()
        return web.Response(status=200)

    async def download_reissued_secret_share(self, request):
        room_id = request.match_info['room_id']
        user_id = request.match_info['user_id']
        room_stored_data = self._rooms_manager.get_room_stored_data(room_id)
        popped_share = room_stored_data.pop_share_by_user(user_id)
        public_numbers = room_stored_data.public_key.public_numbers()
        file_fields = {
            "format_version": room_stored_data.format_version,
            "name": user_id,
            "share_values": popped_share,
            'public_key':
                {
                    'n': str(public_numbers.n),
                    'e': str(public_numbers.e)
                },
            "formula": room_stored_data.new_formula
        }
        json_string = json.dumps(file_fields)
        json_bytes = str.encode(json_string)
        resp_headers = {'Content-Type': 'application/octet-stream',
                        'Content-Disposition': f'attachment; filename="{room_stored_data.identifier}.sss"'}
        return web.Response(body=json_bytes, headers=resp_headers)


class APIVerifySignatureHandler:

    async def verify_signature(self, request):
        try:
            multipart = await request.multipart()
            pdf_binary = None
            pdf_name = "document.pdf"
            public_part_binary = None
            while True:
                part = await multipart.next()
                if part is None:
                    break
                if part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'application/pdf':
                    pdf_binary = bytes(await part.read())
                    if part.filename is not None:
                        pdf_name = part.filename
                elif part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'application/octet-stream':
                    public_part_binary = bytes(await part.read())

            json_string = public_part_binary.decode()
            json_object = json.loads(json_string)
            utils.verify_pdf_signature(pdf_binary, int(json_object['e']), int(json_object['n']))
        except:
            return web.Response(text='WRONG')
        return web.Response(text='OK')


SECRET_CREATION_HANDLER = APISecretCreationHandler()
DOCUMENT_SIGNING_HANDLER = APIDocumentSigningHandler()
SECRET_REISSUE_HANDLER = APISecretReissueHandler()
VERIFY_SIGNATURE_HANDLER = APIVerifySignatureHandler()

ROUTES_LIST = [
    web.post('/createSecretRoom', SECRET_CREATION_HANDLER.create_secret_room),
    web.get('/getSecretRoom', SECRET_CREATION_HANDLER.get_secret_room),
    web.get('/downloadSecretShare/{room_id}/{user_id}', SECRET_CREATION_HANDLER.download_secret_share),
    web.get('/downloadPublicKey/{room_id}', SECRET_CREATION_HANDLER.download_public_key),
    web.post('/createSigningRoom', DOCUMENT_SIGNING_HANDLER.create_signing_room),
    web.get('/getSigningRoom', DOCUMENT_SIGNING_HANDLER.get_signing_room),
    web.get('/downloadOriginalDocument/{room_id}', DOCUMENT_SIGNING_HANDLER.download_original_document),
    web.post('/signDocument', DOCUMENT_SIGNING_HANDLER.sign_document),
    web.post('/finishSigning', DOCUMENT_SIGNING_HANDLER.finish_signing),
    web.get('/downloadSignedDocument/{room_id}', DOCUMENT_SIGNING_HANDLER.download_signed_document),
    web.post('/createSecretReissueRoom', SECRET_REISSUE_HANDLER.create_secret_reissue_room),
    web.get('/getSecretReissueRoom', SECRET_REISSUE_HANDLER.get_secret_reissue_room),
    web.post('/approveSecretReissue', SECRET_REISSUE_HANDLER.approve_secret_reissue),
    web.get('/downloadReissuedSecretShare/{room_id}/{user_id}', SECRET_REISSUE_HANDLER.download_reissued_secret_share),
    web.get('/verifySignature', VERIFY_SIGNATURE_HANDLER.verify_signature)
]
