import struct

class Packet:
    # ! means Big Endian
    # B Unsigned char
    # B unsigned char
    # H unsigned short
    HEADER_FORMAT = '!BBH'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    # Differentiate between data and ack packet
    TYPE_DATA = 0
    TYPE_ACK = 1

    @staticmethod
    def compute_checksum(data: bytes) -> int:
        """
        Computes the 16 bit one's complement sum
        """
        if len(data) % 2 == 1:
            data += b'\x00'

        total_sum = 0
        # sum up 16 bit words
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            total_sum += word

        # Carry around addition
        while (total_sum >> 16):
            total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)

        # Get the 1's complement
        return (~total_sum) & 0xFFFF

    @staticmethod
    def verify_checksum(received_packet: bytes) -> bool:
        """
        Verifies if corrupted by summing all 16-bit words. Valid packets should be 0xFFFF, basically all 1's.
        """
        if len(received_packet) % 2 == 1:
            received_packet += b'\x00'

        total_sum = 0
        for i in range(0, len(received_packet), 2):
            word = (received_packet[i] << 8) + received_packet[i + 1]
            total_sum += word

        while (total_sum >> 16):
            total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)

        return total_sum == 0xFFFF

    @classmethod
    def make_packet(cls, packet_type: int, seq_num: int, payload: bytes = b"") -> bytes:
        """Constructs a binary packet with header and payload combined"""
        # Calculate the checsum
        header_zero_checksum = struct.pack(cls.HEADER_FORMAT, packet_type, seq_num, 0)
        checksum = cls.compute_checksum(header_zero_checksum + payload)

        # Pack the header using struct.pack because struct object will return a byte format structure
        header = struct.pack(cls.HEADER_FORMAT, packet_type, seq_num, checksum)

        return header + payload

    @classmethod
    def extract_packet(cls, packet_bytes: bytes) -> tuple[int, int, bytes, bool]:
        """
        Unpack binary packet.
        Returns type, seq_num, checksum, payload, is_corrupt
        """
        header = packet_bytes[:cls.HEADER_SIZE]
        payload = packet_bytes[cls.HEADER_SIZE:]

        packet_type, seq_num, _ = struct.unpack(cls.HEADER_FORMAT, header)

        # Validate checksum
        is_corrupt = not cls.verify_checksum(packet_bytes)

        return packet_type, seq_num, payload, is_corrupt