from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import utils as cryptography_utils
from cryptography.hazmat.primitives import hashes
from pypdf import PdfReader
from pypdf import PdfWriter
from io import BytesIO
from zlib import crc32
import base64

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


def _adjust_pdf(pdf_data):
    pdf_reader = PdfReader(BytesIO(pdf_data))
    pdf_writer = PdfWriter()
    pdf_writer.append_pages_from_reader(pdf_reader)
    pdf_writer.add_metadata(pdf_reader.metadata)
    bytes_io = BytesIO()
    pdf_writer.write(bytes_io)
    bytes_io.seek(0)
    return bytes_io.read()


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


def add_signature_to_pdf(pdf_data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    adjusted_data = _adjust_pdf(pdf_data)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(adjusted_data)
    hash_value = digest.finalize()
    signature = private_key.sign(
        hash_value,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        cryptography_utils.Prehashed(hashes.SHA256())
    )
    pdf_reader = PdfReader(BytesIO(adjusted_data))
    pdf_writer = PdfWriter()
    pdf_writer.append_pages_from_reader(pdf_reader)
    pdf_writer.add_metadata(pdf_reader.metadata)
    pdf_writer.add_metadata({'/shamir_signature': base64.b64encode(signature).decode('ascii')})
    output_stream = BytesIO()
    pdf_writer.write(output_stream)
    output_stream.seek(0)
    return output_stream.read()


def verify_pdf_signature(pdf_data: bytes, e: int, n: int) -> None:
    public_key = rsa.RSAPublicNumbers(e, n).public_key()
    pdf_reader = PdfReader(BytesIO(pdf_data))
    metadata_values = pdf_reader.metadata.values()
    signature = base64.b64decode(metadata_values.mapping['/shamir_signature'])
    pdf_writer = PdfWriter()
    pdf_writer.append_pages_from_reader(pdf_reader)
    metadata_dict = pdf_reader.metadata
    metadata_dict.pop('/shamir_signature')
    pdf_writer.add_metadata(metadata_dict)
    bytes_io = BytesIO()
    pdf_writer.write(bytes_io)
    bytes_io.seek(0)
    source_pdf_data = bytes_io.read()
    digest = hashes.Hash(hashes.SHA256())
    digest.update(source_pdf_data)
    hash_value = digest.finalize()
    return public_key.verify(signature, hash_value,
                             padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                             cryptography_utils.Prehashed(hashes.SHA256()))
