import socket
import struct

class Packet:
    HEADER_FORMAT = '!BBH'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    TYPE_DATA = 0
    TYPE_ACK = 1

    @staticmethod
    def compute_checksum(data: bytes) -> int:
        if len(data) % 2 == 1:
            data += b'\x00'

        total_sum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            total_sum += word

        while total_sum >> 16:
            total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)

        return (~total_sum) & 0xFFFF

    @staticmethod
    def verify_checksum(packet_bytes: bytes) -> bool:
        if len(packet_bytes) % 2 == 1:
            packet_bytes += b'\x00'

        total_sum = 0
        for i in range(0, len(packet_bytes), 2):
            word = (packet_bytes[i] << 8) + packet_bytes[i + 1]
            total_sum += word

        while total_sum >> 16:
            total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)

        return total_sum == 0xFFFF

    @classmethod
    def make_packet(cls, packet_type: int, seq_num: int, payload: bytes = b"") -> bytes:
        header_zero_checksum = struct.pack(cls.HEADER_FORMAT, packet_type, seq_num, 0)
        checksum = cls.compute_checksum(header_zero_checksum + payload)
        header = struct.pack(cls.HEADER_FORMAT, packet_type, seq_num, checksum)
        return header + payload

    @classmethod
    def extract_packet(cls, packet_bytes: bytes) -> tuple[int, int, bytes, bool]:
        header = packet_bytes[:cls.HEADER_SIZE]
        payload = packet_bytes[cls.HEADER_SIZE:]
        packet_type, seq_num, _ = struct.unpack(cls.HEADER_FORMAT, header)
        is_corrupt = not cls.verify_checksum(packet_bytes)
        return packet_type, seq_num, payload, is_corrupt