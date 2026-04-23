from app.core.sender import Sender
import time

if __name__ == "__main__":
    # Replace with the actual IP address of the server device
    TARGET_IP = "10.0.0.222"
    TARGET_PORT = 12000

    print(f"Initializing RDT 3.0 Sender targetting {TARGET_IP}:{TARGET_PORT}")
    app_client = Sender(TARGET_IP, TARGET_PORT)

    NUM_PACKETS = 2000

    test_payloads = []
    if NUM_PACKETS >= 1:
        test_payloads.append(b"Packet 1: Initialization sequence.")

    for i in range(2, NUM_PACKETS):
        block_letter = chr(65 + ((i - 2) % 26))
        test_payloads.append(f"Packet {i}: Payload block {block_letter}.".encode('utf-8'))

    if NUM_PACKETS >= 2:
        test_payloads.append(f"Packet {NUM_PACKETS}: Termination sequence.".encode('utf-8'))

    for payload in test_payloads:
        print(f"[APPLICATION LAYER] Sending: {payload.decode('utf-8')}")
        app_client.rdt_send(payload)
        #time.sleep(0.2)

    print("Transmission complete.")