from app.core.receiver import Receiver

class ApplicationReceiver(Receiver):
    def deliver_data(self, data: bytes):
        try:
            decoded_message = data.decode('utf-8')
            print(f"[APPLICATION LAYER] Received: {decoded_message}")
        except UnicodeDecodeError:
            print(f"[APPLICATION LAYER] Received raw bytes: {data}")

if __name__ == "__main__":
    LISTEN_IP = "0.0.0.0"
    LISTEN_PORT = 12000

    print(f"Starting RDT 2.2 Receiver on {LISTEN_IP}:{LISTEN_PORT}")
    app_server = ApplicationReceiver(LISTEN_IP, LISTEN_PORT)
    app_server.listen()