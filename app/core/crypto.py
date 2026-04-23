from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os


class CryptoManager:
    def __init__(self, parameters: dh.DHParameters = None):
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

        # State Exposure
        print("\n[CRYPTOGRAPHY] --- Session Key Derivation ---")
        print(f"[CRYPTOGRAPHY] Local Private Key (x): 0x{hex(self.private_key.private_numbers().x)[2:32]}...")
        print(f"[CRYPTOGRAPHY] Local Public Key (y):  0x{hex(self.public_key.public_numbers().y)[2:32]}...")
        print(f"[CRYPTOGRAPHY] Raw Shared Secret:     0x{shared_secret.hex()[:30]}...")
        print(f"[CRYPTOGRAPHY] Derived AES-256 Key:   0x{derived_key.hex()}")
        print("[CRYPTOGRAPHY] ------------------------------\n")

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)
        payload = nonce + ciphertext

        # State Exposure
        print(f"\n[CRYPTOGRAPHY] --- Encryption Operation ---")
        print(f"[CRYPTOGRAPHY] Plaintext:  {plaintext}")
        print(f"[CRYPTOGRAPHY] Nonce (12B): 0x{nonce.hex()}")
        print(f"[CRYPTOGRAPHY] Ciphertext: 0x{ciphertext.hex()}")
        print(f"[CRYPTOGRAPHY] Payload:    0x{payload.hex()}")

        return payload

    def decrypt(self, ciphertext: bytes) -> bytes:
        nonce = ciphertext[:12]
        actual_ciphertext = ciphertext[12:]

        # State Exposure
        print(f"\n[CRYPTOGRAPHY] --- Decryption Operation ---")
        print(f"[CRYPTOGRAPHY] Raw Payload: 0x{ciphertext.hex()}")
        print(f"[CRYPTOGRAPHY] Extr Nonce:  0x{nonce.hex()}")
        print(f"[CRYPTOGRAPHY] Extr Cipher: 0x{actual_ciphertext.hex()}")

        plaintext = self.aesgcm.decrypt(nonce, actual_ciphertext, None)
        print(f"[CRYPTOGRAPHY] Decrypted:   {plaintext}")

        return plaintext