from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.serialization import load_der_private_key
from zlib import crc32

SERIALIZATION_ENDIAN = "little"


class PrivateKeyChecksumError(Exception):
    pass


def _byte_length(integer: int) -> int:
    return (integer.bit_length() + 7) // 8


def _restore_private_key(n: int, e: int, d: int) -> rsa.RSAPrivateKey:
    p, q = rsa.rsa_recover_prime_factors(n, e, d)
    iqmp = rsa.rsa_crt_iqmp(p, q)
    dmp1 = rsa.rsa_crt_dmp1(d, p)
    dmq1 = rsa.rsa_crt_dmp1(d, q)
    return rsa.RSAPrivateNumbers(p, q, d, dmp1, dmq1, iqmp, rsa.RSAPublicNumbers(e, n)).private_key()


def private_key_to_int(private_key: rsa.RSAPrivateKey) -> int:
    key_d = private_key.private_numbers().d
    key_d_bytes = key_d.to_bytes(_byte_length(key_d), SERIALIZATION_ENDIAN)
    checksum = crc32(key_d_bytes)
    key_d_bytes += checksum.to_bytes(4, SERIALIZATION_ENDIAN)
    key_d_bytes += bytes([1])  # prevent bytes loss
    return int.from_bytes(key_d_bytes, SERIALIZATION_ENDIAN)


def int_to_private_key(converted_key: int, public_key: rsa.RSAPublicKey) -> rsa.RSAPrivateKey:
    raw_bytes = converted_key.to_bytes(_byte_length(converted_key), SERIALIZATION_ENDIAN)
    checksum_bytes = raw_bytes[-5:-1]
    checksum = int.from_bytes(checksum_bytes, SERIALIZATION_ENDIAN)
    key_d_bytes = raw_bytes[:-5]
    if crc32(key_d_bytes) != checksum:
        raise PrivateKeyChecksumError()
    return _restore_private_key(public_key.public_numbers().n, public_key.public_numbers().e,
                                int.from_bytes(key_d_bytes, SERIALIZATION_ENDIAN))
