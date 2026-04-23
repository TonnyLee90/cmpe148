from app.core.sender import Sender
import time

if __name__ == "__main__":
    # Replace with the actual IP address of the server device
    TARGET_IP = "192.168.1.X"
    TARGET_PORT = 12000

    print(f"Initializing RDT 3.0 Sender targetting {TARGET_IP}:{TARGET_PORT}")
    app_client = Sender(TARGET_IP, TARGET_PORT)

    test_payloads = [
        b"Packet 1: Initialization sequence.",
        b"Packet 2: Payload block A.",
        b"Packet 3: Payload block B.",
        b"Packet 4: Termination sequence."
    ]

    for payload in test_payloads:
        print(f"[APPLICATION LAYER] Sending: {payload.decode('utf-8')}")
        app_client.rdt_send(payload)
        time.sleep(1)

    print("Transmission complete.")