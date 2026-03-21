import socket
from packet import Packet

# States
# WAIT_CALL_0: 0
# WAIT_ACK_0: 1
# WAIT_CALL_1: 2
# WAIT_ACK_1: 3

class Sender:
    def __init__(self, target_ip: str, target_port: int):
        self.target_address = (target_ip, target_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1.0) # RDT 3.0 timer capability
        self.state = 0  # WAIT_CALL_0

    def rdt_send(self, data: bytes):
        if self.state == 0:  # WAIT_CALL_0
            # make_pkt(0, data, checksum)
            sndpkt = Packet.make_packet(Packet.TYPE_DATA, 0, data)

            # udt_send(sndpkt)
            self.sock.sendto(sndpkt, self.target_address)

            # start_timer (handled by socket timeout)
            # Transition
            self.state = 1  # WAIT_ACK_0
            self.wait_for_ack_0()

    def wait_for_ack_0(self):
        # Blocking wait for ACK
        try:
            rcvpkt, _ = self.sock.recvfrom(1024)
            packet_type, seq_num, payload, is_corrupt = Packet.extract_packet(rcvpkt)

            # rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && isACK(rcvpkt,0)
            if not is_corrupt and packet_type == Packet.TYPE_ACK and seq_num == 0:
                # stop_timer (implicit upon receiving)
                # Transition
                self.state = 2  # WAIT_CALL_1
        except socket.timeout:
            # Timeout logic deferred to subsequent implementation steps
            pass