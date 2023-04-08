from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.serialization import load_der_private_key
from zlib import crc32

SERIALIZATION_ENDIAN = "little"


class PrivateKeyChecksumError(Exception):
    pass


def _byte_length(integer: int) -> int:
    return (integer.bit_length() + 7) // 8


def private_key_to_int(private_key: rsa.RSAPrivateKey) -> int:
    serialized_key = private_key.private_bytes(crypto_serialization.Encoding.DER,
                                               crypto_serialization.PrivateFormat.TraditionalOpenSSL,
                                               crypto_serialization.NoEncryption())
    checksum = crc32(serialized_key)
    serialized_key += checksum.to_bytes(4, SERIALIZATION_ENDIAN)
    serialized_key += bytes([1])  # prevent bytes loss
    return int.from_bytes(serialized_key, SERIALIZATION_ENDIAN)


def int_to_private_key(converted_key: int) -> rsa.RSAPrivateKey:
    raw_bytes = converted_key.to_bytes(_byte_length(converted_key), SERIALIZATION_ENDIAN)
    checksum_bytes = raw_bytes[-5:-1]
    checksum = int.from_bytes(checksum_bytes, SERIALIZATION_ENDIAN)
    key_bytes = raw_bytes[:-5]
    if crc32(key_bytes) != checksum:
        raise PrivateKeyChecksumError()
    return load_der_private_key(key_bytes, password=None)
