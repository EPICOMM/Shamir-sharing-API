from datetime import datetime
from server.utils import utils
import server.shamath.__init__ as shamir_math_module
from cryptography.hazmat.primitives.asymmetric import rsa
from Crypto.Util import number
import random
import string

CONFIGURATION_MODULO = number.getPrime(4096 + 128)


def _generate_room_id() -> str:
    id_result = ""
    for block in range(4):
        for letter in range(3):
            id_result += random.choice(string.ascii_letters)
        if block != 3:
            id_result += "-"


class SecretCreationRoomStoredData:
    creation_datetime: datetime
    identifier: str
    participants_shares: list[shamir_math_module.Part]
    public_key: rsa.RSAPublicKey
    formula: str
    format_version: int

    def __init__(self, key_splitted: list[shamir_math_module.Part], public_key: rsa.RSAPublicKey, formula: str,
                 format_version: int):
        self.creation_datetime = datetime.now()
        self.identifier = _generate_room_id()
        self.participants_shares = key_splitted
        self.public_key = public_key
        self.formula = formula
        self.format_version = format_version

    def pop_share_by_user(self, user_id: str) -> shamir_math_module.Part:
        for user in self.participants_shares:
            if user.name == user_id:
                to_return = user.values
                user.values = None
                return to_return
        raise Exception()


class SecretCreationRoomsManager:
    _stored_rooms: list[SecretCreationRoomStoredData]

    def __init__(self):
        self._stored_rooms = []

    def create_room(self, participants_lists: list, formula: str) -> str:
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        key_int = utils.private_key_to_int(key)
        configuration = shamir_math_module.Configuration(modulo=CONFIGURATION_MODULO, formula=formula)
        key_splitted = configuration.split(key_int)
        new_room = SecretCreationRoomStoredData(key.public_key(), key_splitted)
        self._stored_rooms.append(new_room)
        return new_room.identifier


    def get_room_stored_data(self, room_id: str) -> SecretCreationRoomStoredData:
        for room in self._stored_rooms:
            if room.identifier == room_id:
                return room
        raise Exception()
