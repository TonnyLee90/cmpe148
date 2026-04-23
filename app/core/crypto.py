from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class CryptoManager:
    def __init__(self, parameters: dh.DHParameters = None):
        """
        Generates 2048-bit DH parameters if none provided.
        Generation takes time. In production, pre-generate or use RFC 3526 standards.
        """
        self.parameters = parameters or dh.generate_parameters(generator=2, key_size=2048)
        self.private_key = self.parameters.generate_private_key()
        self.public_key = self.private_key.public_key()
        self.aesgcm = None

    def get_public_bytes(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def get_parameter_bytes(self) -> bytes:
        return self.parameters.parameter_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.ParameterFormat.PKCS3
        )

    def establish_session(self, peer_public_bytes: bytes):
        peer_public_key = serialization.load_pem_public_key(peer_public_bytes)
        shared_secret = self.private_key.exchange(peer_public_key)

        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(shared_secret)

        self.aesgcm = AESGCM(derived_key)

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        nonce = ciphertext[:12]
        actual_ciphertext = ciphertext[12:]
        return self.aesgcm.decrypt(nonce, actual_ciphertext, None)

if __name__ == "__main__":
    pass