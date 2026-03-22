import socket
from packet import Packet

# States
# WAIT_0_FROM_BELOW: 0
# WAIT_1_FROM_BELOW: 1

class Receiver:
    def __init__(self, listen_ip: str, listen_port: int):
        self.listen_address = (listen_ip, listen_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.listen_address)
        self.state = 0  # WAIT_0_FROM_BELOW

    def listen(self):
        while True:
            rcvpkt, sender_address = self.sock.recvfrom(1024)
            packet_type, seq_num, payload, is_corrupt = Packet.extract_packet(rcvpkt)

            if self.state == 0:  # WAIT_0_FROM_BELOW
                if is_corrupt or (packet_type == Packet.TYPE_DATA and seq_num == 1):
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 1)
                    self.sock.sendto(ack_pkt, sender_address)

                # rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && has_seq0(rcvpkt)
                elif not is_corrupt and packet_type == Packet.TYPE_DATA and seq_num == 0:
                    # extract(rcvpkt, data) -> payload
                    # deliver_data(data)
                    self.deliver_data(payload)

                    # sndpkt = make_pkt(ACK, 0, checksum)
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 0)

                    # udt_send(sndpkt)
                    self.sock.sendto(ack_pkt, sender_address)

                    # Transition
                    self.state = 1  # WAIT_1_FROM_BELOW

            elif self.state == 1:  # WAIT_1_FROM_BELOW
                if is_corrupt or (packet_type == Packet.TYPE_DATA and seq_num == 0):
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 0)
                    self.sock.sendto(ack_pkt, sender_address)
                elif not is_corrupt and packet_type == Packet.TYPE_DATA and seq_num == 1:
                    self.deliver_data(payload)
                    ack_pkt = Packet.make_packet(Packet.TYPE_ACK, 1)
                    self.sock.sendto(ack_pkt, sender_address)
                    self.state = 0  # WAIT_0_FROM_BELOW

    def deliver_data(self, data: bytes):
        # handoff to Application layer
        pass