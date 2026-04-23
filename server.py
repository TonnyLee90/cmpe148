from app.core.receiver import Receiver

import socket
from cryptography.hazmat.primitives import serialization
from app.core.crypto import CryptoManager


class SecureApplicationReceiver(Receiver):
    def __init__(self, listen_ip: str, listen_port: int, crypto_manager: CryptoManager):
        super().__init__(listen_ip, listen_port)
        self.crypto_manager = crypto_manager

    def deliver_data(self, data: bytes):
        try:
            plaintext = self.crypto_manager.decrypt(data)
            print(f"[APPLICATION LAYER] Decrypted: {plaintext.decode('utf-8')}")
        except Exception as e:
            print(f"[APPLICATION LAYER] Decryption failed: {e}")


def execute_server_handshake(listen_ip: str, handshake_port: int) -> CryptoManager:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_ip, handshake_port))

    print("[HANDSHAKE] Waiting for client parameters and public key...")
    client_data, client_addr = sock.recvfrom(4096)

    # Extract client parameters and key (delimited by custom separator)
    param_bytes, client_pub_bytes = client_data.split(b'|||')
    parameters = serialization.load_pem_parameters(param_bytes)

    # Initialize server crypto with client's parameters
    crypto = CryptoManager(parameters)

    # Send server public key back to client
    print("[HANDSHAKE] Transmitting server public key...")
    sock.sendto(crypto.get_public_bytes(), client_addr)

    # Establish shared AES key
    crypto.establish_session(client_pub_bytes)
    print("[HANDSHAKE] Session key established.")

    sock.close()
    return crypto


if __name__ == "__main__":
    LISTEN_IP = "0.0.0.0"
    HANDSHAKE_PORT = 11999
    RDT_PORT = 12000

    server_crypto = execute_server_handshake(LISTEN_IP, HANDSHAKE_PORT)

    print(f"Starting Secure RDT 2.2 Receiver on {LISTEN_IP}:{RDT_PORT}")
    app_server = SecureApplicationReceiver(LISTEN_IP, RDT_PORT, server_crypto)
    app_server.listen()