import socket
from packet import Packet

# States
# WAIT_CALL_0: 0
# WAIT_ACK_0: 1
# WAIT_CALL_1: 2
# WAIT_ACK_1: 3

class Sender:
    """RDT 3.0 Sender FSM"""

    def __init__(self, target_ip: str, target_port: int, timeout: float = 2.0):
        self.target_address = (target_ip, target_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.timeout = timeout
        self.sock.settimeout(self.timeout)
        self.state = 0  # 0: WAIT_CALL_0, 1: WAIT_ACK_0, 2: WAIT_CALL_1, 3: WAIT_ACK_1
        self.last_sndpkt = b''

    def _flush_buffer(self):
        self.sock.setblocking(False)
        while True:
            try:
                self.sock.recvfrom(1024)
            except (BlockingIOError, socket.error):
                break
        self.sock.settimeout(self.timeout)

    def rdt_send(self, data: bytes):
        self._flush_buffer()

        if self.state == 0:
            self.last_sndpkt = Packet.make_packet(Packet.TYPE_DATA, 0, data)
            self.sock.sendto(self.last_sndpkt, self.target_address)
            self.state = 1
            self.wait_for_ack_0()

        elif self.state == 2:
            self.last_sndpkt = Packet.make_packet(Packet.TYPE_DATA, 1, data)
            self.sock.sendto(self.last_sndpkt, self.target_address)
            self.state = 3
            self.wait_for_ack_1()

    def wait_for_ack_0(self):
        while True:
            try:
                rcvpkt, _ = self.sock.recvfrom(1024)
                packet_type, seq_num, payload, is_corrupt = Packet.extract_packet(rcvpkt)

                # rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || isACK(rcvpkt,1)) -> Λ
                if is_corrupt or (packet_type == Packet.TYPE_ACK and seq_num == 1):
                    continue

                    # rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && isACK(rcvpkt,0)
                if not is_corrupt and packet_type == Packet.TYPE_ACK and seq_num == 0:
                    self.state = 2
                    break
            except socket.timeout:
                # timeout -> udt_send(sndpkt), start_timer
                self.sock.sendto(self.last_sndpkt, self.target_address)

    def wait_for_ack_1(self):
        while True:
            try:
                rcvpkt, _ = self.sock.recvfrom(1024)
                packet_type, seq_num, payload, is_corrupt = Packet.extract_packet(rcvpkt)

                # rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || isACK(rcvpkt,0)) -> Λ
                if is_corrupt or (packet_type == Packet.TYPE_ACK and seq_num == 0):
                    continue

                    # rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && isACK(rcvpkt,1)
                if not is_corrupt and packet_type == Packet.TYPE_ACK and seq_num == 1:
                    self.state = 0
                    break
            except socket.timeout:
                # timeout -> udt_send(sndpkt), start_timer
                self.sock.sendto(self.last_sndpkt, self.target_address)