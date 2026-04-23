from app.core.sender import Sender
import time

import socket
import time
from app.core.crypto import CryptoManager


def execute_client_handshake(target_ip: str, handshake_port: int) -> CryptoManager:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)

    print("[HANDSHAKE] Generating DH Parameters (This may take a moment)...")
    crypto = CryptoManager()

    payload = crypto.get_parameter_bytes() + b'|||' + crypto.get_public_bytes()

    print("[HANDSHAKE] Transmitting parameters and public key...")
    sock.sendto(payload, (target_ip, handshake_port))

    try:
        server_pub_bytes, _ = sock.recvfrom(4096)
        crypto.establish_session(server_pub_bytes)
        print("[HANDSHAKE] Session key established.")
    except socket.timeout:
        raise TimeoutError("Handshake failed: No response from server.")
    finally:
        sock.close()

    return crypto


if __name__ == "__main__":
    TARGET_IP = "10.0.0.222"  # Update to exact server IP
    HANDSHAKE_PORT = 11999
    RDT_PORT = 12000
    NUM_PACKETS = 10

    client_crypto = execute_client_handshake(TARGET_IP, HANDSHAKE_PORT)

    print(f"Initializing Secure RDT 3.0 Sender targeting {TARGET_IP}:{RDT_PORT}")
    app_client = Sender(TARGET_IP, RDT_PORT)

    test_payloads = []
    if NUM_PACKETS >= 1:
        test_payloads.append(b"Packet 1: Initialization sequence.")

    for i in range(2, NUM_PACKETS):
        block_letter = chr(65 + ((i - 2) % 26))
        test_payloads.append(f"Packet {i}: Payload block {block_letter}.".encode('utf-8'))

    if NUM_PACKETS >= 2:
        test_payloads.append(f"Packet {NUM_PACKETS}: Termination sequence.".encode('utf-8'))

    for payload in test_payloads:
        print(f"\n[APPLICATION LAYER] Original data: {payload.decode('utf-8')}")
        encrypted_payload = client_crypto.encrypt(payload)
        app_client.rdt_send(encrypted_payload)
        time.sleep(1)

    print("Transmission complete.")