from datetime import datetime
from server.utils import utils
import secret_sharing.__init__ as shamir_math_module
from cryptography.hazmat.primitives.asymmetric import rsa
import random
import string

CONFIGURATION_MODULO = int("2889319989747198508017897377754761759953328277718754812082417603477570842702413950136716111"
                           "4253125522907640180566965220783523146817894334026799437526739377193559559759889067003401856"
                           "2124498386860955753009768466817083708333848035385454268746020077331016479520447589046833952"
                           "2468447831807449528626388788175819759513387131120380099136954031597223791057532693555922087"
                           "7080849132050876432134809102256797707118419261526971400407236775453157270483476375406065843"
                           "5319702302382464271892705571752173635918220535458342355913957812656303041229955422952783952"
                           "0253165732173318673267943281002269301242411985438368757907751355332784816919907385242939906"
                           "9177591601361748211345865728344666332255374851560507057003634209145392689495403329031170379"
                           "1014981854500023650703167852063741648305428020847503987261709990908729830410603464119293967"
                           "7228304604770738512134171769815854161435373798859091868613291882864749563180319597248091170"
                           "2085579557384687374818316304547016994826324567709075147295589914766965537838037352562465293"
                           "5744425590033704088141455053437189109095709767466367466947490692741916306743994840604477651"
                           "0821456681379928554673026860125006056160091726631821837704458773169723051070221270445735400"
                           "48557191607576051060248378262129303185824081872165173389833458016853826300737741498501823")


def _generate_room_id() -> str:
    id_result = ""
    for block in range(4):
        for letter in range(3):
            id_result += random.choice(string.ascii_letters)
        if block != 3:
            id_result += "-"
    return id_result


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

    def pop_share_by_user(self, user_id: str) -> list[int]:
        for index, user in enumerate(self.participants_shares):
            if user.name == user_id and user.values is not None:
                to_return = user.values
                self.participants_shares[index].values = None
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
        new_room = SecretCreationRoomStoredData(key_splitted, key.public_key(), formula, 1)
        self._stored_rooms.append(new_room)
        return new_room.identifier

    def get_room_stored_data(self, room_id: str) -> SecretCreationRoomStoredData:
        for room in self._stored_rooms:
            if room.identifier == room_id:
                return room
        raise Exception()


class DocumentSigningRoomStoredData:
    creation_datetime: datetime
    identifier: str
    creator_token: str
    participants_shares: list[shamir_math_module.Part]
    participants_count: int
    public_key: rsa.RSAPublicKey
    formula: str
    pdf_binary: bytes
    pdf_name: str
    signed_pdf_binary: bytes
    format_version: int

    def __init__(self, initial_share: shamir_math_module.Part, public_key: rsa.RSAPublicKey, formula: str,
                 pdf_binary: bytes, pdf_name: str, format_version: int):
        self.creation_datetime = datetime.now()
        self.identifier = _generate_room_id()
        self.creator_token = _generate_room_id()
        self.participants_shares = [initial_share]
        self.public_key = public_key
        self.pdf_binary = pdf_binary
        self.pdf_name = pdf_name
        self.formula = formula
        self.signed_pdf_binary = None
        self.format_version = format_version
        self._configuration = shamir_math_module.Configuration(modulo=CONFIGURATION_MODULO, formula=formula)
        self.participants_count = len(self._configuration.names())

    def add_share(self, name: str, share_values: list[int]):
        self.participants_shares.append(shamir_math_module.Part(name, share_values))

    def finish_signing(self, creator_token: str) -> bool:
        restored_secret = self._configuration.restore(self.participants_shares)
        restored_key = utils.int_to_private_key(restored_secret, self.public_key)
        self.signed_pdf_binary = utils.add_signature_to_pdf(self.pdf_binary, restored_key)
        return 0

    def signing_available(self) -> bool:
        if self._configuration.restore(self.participants_shares) is not None:
            return True
        return False


class DocumentSigningRoomsManager:
    _stored_rooms: list[SecretCreationRoomStoredData]

    def __init__(self):
        self._stored_rooms = []

    def create_room(self, name: str, values: list[int], public_n: int, public_e: int, formula: str,
                    pdf_binary: bytes, pdf_name: str, format_version: int) -> (str, str):
        new_room = DocumentSigningRoomStoredData(shamir_math_module.Part(name, values),
                                                 rsa.RSAPublicNumbers(public_e, public_n).public_key(),
                                                 formula,
                                                 pdf_binary, pdf_name, format_version)
        self._stored_rooms.append(new_room)
        return new_room.identifier, new_room.creator_token

    def get_room_stored_data(self, room_id: str) -> DocumentSigningRoomStoredData:
        for room in self._stored_rooms:
            if room.identifier == room_id:
                return room
        raise Exception()


class SecretReissueRoomStoredData:
    creation_datetime: datetime
    identifier: str
    participants_shares: list[shamir_math_module.Part]
    formula: str
    new_formula: str
    participants_new_shares: list[shamir_math_module.Part]
    participants_count: int
    format_version: int
    public_key: rsa.RSAPublicKey
    _configuration: shamir_math_module.Configuration
    _new_configuration: shamir_math_module.Configuration

    def __init__(self, initial_share: shamir_math_module.Part, public_key: rsa.RSAPublicKey, formula: str,
                 new_formula: str,
                 format_version: int):
        self.creation_datetime = datetime.now()
        self.identifier = _generate_room_id()
        self.participants_shares = [initial_share]
        self.formula = formula
        self.new_formula = new_formula
        self.format_version = format_version
        self.participants_new_shares = None
        self._configuration = shamir_math_module.Configuration(modulo=CONFIGURATION_MODULO, formula=formula,
                                                               version=format_version)
        self._new_configuration = shamir_math_module.Configuration(modulo=CONFIGURATION_MODULO, formula=new_formula,
                                                                   version=format_version)
        self.participants_count = len(self._configuration.names())
        self.public_key = public_key

    def add_share(self, name: str, share_values: list[int]):
        self.participants_shares.append(shamir_math_module.Part(name, share_values))

    def pop_share_by_user(self, user_id: str) -> shamir_math_module.Part:
        def pop_share_by_user(self, user_id: str) -> list[int]:
            for index, user in enumerate(self.participants_new_shares):
                if user.name == user_id and user.values is not None:
                    to_return = user.values
                    self.participants_new_shares[index].values = None
                    return to_return
            raise Exception()

    def try_reissue(self) -> bool:
        try:
            self.participants_new_shares = self._configuration.modify(self._new_configuration, self.participants_shares)
        except:
            return 1
        return 0


class SecretReissueRoomsManager:
    _stored_rooms: list[SecretReissueRoomStoredData]

    def __init__(self):
        self._stored_rooms = []

    def create_room(self, initial_share_name: str, initial_share_value: int, public_n: int, public_e: int, formula: str,
                    new_formula: str,
                    format_version: int) -> str:
        new_room = SecretReissueRoomStoredData(shamir_math_module.Part(initial_share_name, initial_share_value),
                                               rsa.RSAPublicNumbers(public_e, public_n).public_key(),
                                               formula, new_formula, format_version)
        self._stored_rooms.append(new_room)
        return new_room.identifier

    def get_room_stored_data(self, room_id: str) -> SecretReissueRoomStoredData:
        for room in self._stored_rooms:
            if room.identifier == room_id:
                return room
        raise Exception()
