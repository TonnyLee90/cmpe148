import socket
from app.core.simple_packet import Packet
import random

# States
# WAIT_0_FROM_BELOW: 0
# WAIT_1_FROM_BELOW: 1

class Receiver:
    STATE_MAP = {0: "WAIT_0_FROM_BELOW", 1: "WAIT_1_FROM_BELOW"}

    def __init__(self, listen_ip: str, listen_port: int):
        self.listen_address = (listen_ip, listen_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.listen_address)
        self.state = 0
        self._log_state()

    def _udt_send(self, packet_bytes: bytes, target_address: tuple, corrupt_prob: float = 0.05):
        """
        Simulates an unreliable network by occasionally corrupting the packet
        before sending it through the actual UDP socket.
        """
        if random.random() < corrupt_prob:
            print(f">>> [NETWORK SIMULATOR] Injecting bit-error into packet for {target_address}!")
            # Convert to bytearray because standard bytes are immutable
            corrupted_packet = bytearray(packet_bytes)

            # Pick a random byte index to corrupt (can be header or payload)
            random_index = random.randint(0, len(corrupted_packet) - 1)

            # XOR the byte with 0xFF to flip its bits, ensuring the checksum will fail
            corrupted_packet[random_index] ^= 0xFF

            # Send the intentionally corrupted packet
            self.sock.sendto(bytes(corrupted_packet), target_address)
        else:
            # Send normally
            self.sock.sendto(packet_bytes, target_address)

    def _log_state(self):
        print(f"\n[RECEIVER STATE] Current: {self.STATE_MAP[self.state]}")

    def listen(self):
        print("[RECEIVER ACTION] Listening for incoming packets...")
        while True:
            rcvpkt, sender_address = self.sock.recvfrom(1024)
            packet_type, seq_num, payload, is_corrupt = Packet.extract_packet(rcvpkt)

            type_str = "ACK" if packet_type == Packet.TYPE_ACK else "DATA"
            print(f"[RECEIVER RECV] Received {type_str} {seq_num} | Corrupt: {is_corrupt}")

            if self.state == 0:
                if is_corrupt or (packet_type == Packet.TYPE_DATA and seq_num == 1):
                    print("[RECEIVER ACTION] Packet corrupt or wrong sequence. Transmitting duplicate ACK 1.")
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 1)
                    self._udt_send(ack_pkt, sender_address)
                elif not is_corrupt and packet_type == Packet.TYPE_DATA and seq_num == 0:
                    print("[RECEIVER ACTION] Valid Pkt 0 received. Delivering data and transmitting ACK 0.")
                    self.deliver_data(payload)
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 0)
                    self._udt_send(ack_pkt, sender_address)
                    self.state = 1
                    self._log_state()

            elif self.state == 1:
                if is_corrupt or (packet_type == Packet.TYPE_DATA and seq_num == 0):
                    print("[RECEIVER ACTION] Packet corrupt or wrong sequence. Transmitting duplicate ACK 0.")
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 0)
                    self._udt_send(ack_pkt, sender_address)

                elif not is_corrupt and packet_type == Packet.TYPE_DATA and seq_num == 1:
                    print("[RECEIVER ACTION] Valid Pkt 1 received. Delivering data and transmitting ACK 1.")
                    self.deliver_data(payload)
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 1)
                    self._udt_send(ack_pkt, sender_address)
                    self.state = 0
                    self._log_state()

    def deliver_data(self, data: bytes):
        pass