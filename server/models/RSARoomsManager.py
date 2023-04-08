from datetime import datetime
from server.utils import utils
import server.shamath.__init__ as shamir_math_module
from cryptography.hazmat.primitives.asymmetric import rsa
from typing import Any
import random
import string


def _generate_room_id() -> str:
    id_result = ""
    for block in range(4):
        for letter in range(3):
            id_result += random.choice(string.ascii_letters)
        if block != 3:
            id_result += "-"


class RoomStoredData:
    def __init__(self, key_splitted: list[tuple[Any, int]], public_key_param: rsa.RSAPublicKey):
        self.creation_datetime = datetime.now()
        self.identifier = _generate_room_id()
        self.participants_shares = key_splitted
        self.public_key = public_key_param


class RSARoomsManager:
    def __init__(self):
        self._stored_rooms = []

    def create_room(self, participants_lists: list, formula: str) -> str:
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        key_int = utils.private_key_to_int(key)
        configuration = shamir_math_module.Configuration(modulo=257, formula=formula)
        key_splitted = configuration.split(key_int)
        new_room = RoomStoredData(key.public_key(), key_splitted)
        self._stored_rooms.append(new_room)
        return new_room.identifier
