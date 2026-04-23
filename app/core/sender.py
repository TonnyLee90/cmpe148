import socket
from app.core.simple_packet import Packet
import random

# States
# WAIT_CALL_0: 0
# WAIT_ACK_0: 1
# WAIT_CALL_1: 2
# WAIT_ACK_1: 3

class Sender:
    STATE_MAP = {0: "WAIT_CALL_0", 1: "WAIT_ACK_0", 2: "WAIT_CALL_1", 3: "WAIT_ACK_1"}

    def __init__(self, target_ip: str, target_port: int, timeout: float = 2.0):
        self.target_address = (target_ip, target_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.timeout = timeout
        self.sock.settimeout(self.timeout)
        self.state = 0
        self.last_sndpkt = b''
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
        print(f"[SENDER STATE] Current: {self.STATE_MAP[self.state]}")

    def _flush_buffer(self):
        self.sock.setblocking(False)
        flushed = 0
        while True:
            try:
                self.sock.recvfrom(1024)
                flushed += 1
            except (BlockingIOError, socket.error):
                break
        self.sock.settimeout(self.timeout)
        if flushed > 0:
            print(f"[SENDER BUFFER] Flushed {flushed} stale packet(s) via Λ transition.")

    def rdt_send(self, data: bytes):
        print(f"\n[SENDER ACTION] Application called rdt_send().")
        self._flush_buffer()

        if self.state == 0:
            self.last_sndpkt = Packet.make_packet(Packet.TYPE_DATA, 0, data)
            print("[SENDER ACTION] Transmitting Pkt 0.")
            self._udt_send(self.last_sndpkt, self.target_address)
            self.state = 1
            self._log_state()
            self.wait_for_ack_0()

        elif self.state == 2:
            self.last_sndpkt = Packet.make_packet(Packet.TYPE_DATA, 1, data)
            print("[SENDER ACTION] Transmitting Pkt 1.")
            self._udt_send(self.last_sndpkt, self.target_address)
            self.state = 3
            self._log_state()
            self.wait_for_ack_1()

    def wait_for_ack_0(self):
        while True:
            try:
                rcvpkt, _ = self.sock.recvfrom(1024)
                packet_type, seq_num, payload, is_corrupt = Packet.extract_packet(rcvpkt)

                type_str = "ACK" if packet_type == Packet.TYPE_ACK else "DATA"
                print(f"[SENDER RECV] Received {type_str} {seq_num} | Corrupt: {is_corrupt}")

                if is_corrupt or (packet_type == Packet.TYPE_ACK and seq_num == 1):
                    print("[SENDER ACTION] Invalid/Duplicate ACK. Ignoring (Λ).")
                    continue

                if not is_corrupt and packet_type == Packet.TYPE_ACK and seq_num == 0:
                    print("[SENDER ACTION] Valid ACK 0 received. Transitioning.")
                    self.state = 2
                    self._log_state()
                    break
            except socket.timeout:
                print("[SENDER TIMEOUT] Timer expired. Retransmitting Pkt 0.")
                self._udt_send(self.last_sndpkt, self.target_address)

    def wait_for_ack_1(self):
        while True:
            try:
                rcvpkt, _ = self.sock.recvfrom(1024)
                packet_type, seq_num, payload, is_corrupt = Packet.extract_packet(rcvpkt)

                type_str = "ACK" if packet_type == Packet.TYPE_ACK else "DATA"
                print(f"[SENDER RECV] Received {type_str} {seq_num} | Corrupt: {is_corrupt}")

                if is_corrupt or (packet_type == Packet.TYPE_ACK and seq_num == 0):
                    print("[SENDER ACTION] Invalid/Duplicate ACK. Ignoring (Λ).")
                    continue

                if not is_corrupt and packet_type == Packet.TYPE_ACK and seq_num == 1:
                    print("[SENDER ACTION] Valid ACK 1 received. Transitioning.")
                    self.state = 0
                    self._log_state()
                    break
            except socket.timeout:
                print("[SENDER TIMEOUT] Timer expired. Retransmitting Pkt 1.")
                self._udt_send(self.last_sndpkt, self.target_address)