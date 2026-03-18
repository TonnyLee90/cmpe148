import struct

"""
A packet is just a chunk of bytes you send over UDP. 
Define our own application layer header called CALP
"""
# Header format: SEQ (4 bytes) | ACK (4 bytes) | FLAGS (1 byte) | WIN (2 bytes) | LEN (2 bytes)
# Total header = 13 bytes

# This is a format string that tells struct how to pack/unpack bytes
"""
!: big-endian (network byte order) 0 bytes
I: unsigned int (SEQ and ACK) 4 bytes each
B: unsigned char(FLAGS) 1
H: unsigned short (WIN and LEN)2
"""
HEADER_FORMAT = '!IIBHH'

HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # should be 13
MAX_PAYLOAD = 1024

# FLAGS
"""
Bit:   7  6  5  4  3  2  1  0
       0  0  0  0  0  0  0  1  ← SYN  = 0b00000001 = 1
       0  0  0  0  0  0  1  0  ← ACK  = 0b00000010 = 2
       0  0  0  0  0  1  0  0  ← FIN  = 0b00000100 = 4
       0  0  0  0  1  0  0  0  ← RST  = 0b00001000 = 8
       0  0  0  1  0  0  0  0  ← DATA = 0b00010000 = 16
"""
FLAG_SYN  = 0b00000001
FLAG_ACK  = 0b00000010
FLAG_FIN  = 0b00000100
FLAG_RST  = 0b00001000
FLAG_DATA = 0b00010000

# Define packet
class Packet:
    def __init__(self, seq, ack, flags, window, payload=b''):
        self.seq     = seq # sequence number — which packet # this is (1, 2, 3, ...)
        self.ack     = ack # acknowledgement — what is the # of the next packet you want to receive (1, 2, 3, ...)
        self.flags   = flags # which flags are on (SYN/ACK/FIN/DATA) (0b00010000)
        self.window  = window # how many packets receiver can accept (8)
        self.payload = payload # the actual data being sent (b"hello")

    # "struct.pack" turns the Python integers into raw bytes using the format. 
    # then concatenate the header bytes and payload bytes together (this is what we sent over UDP)
    def encode(self):
        header = struct.pack(HEADER_FORMAT, 
                             self.seq, self.ack, self.flags,
                             self.window, len(self.payload))
        return header + self.payload

    # takes raw bytes coming off the socket and reconstructs a Packet object.
    @staticmethod # means the method doesn't need self; it doesn't belong to any specific instance of the class.
    def decode(data):
        seq, ack, flags, window, length = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE]) # first 13 bytes → the header
        payload = data[HEADER_SIZE:HEADER_SIZE + length] #  slices the payload right after it.
        return Packet(seq, ack, flags, window, payload)

    def is_ack(self):  return bool(self.flags & FLAG_ACK)
    def is_syn(self):  return bool(self.flags & FLAG_SYN)
    def is_fin(self):  return bool(self.flags & FLAG_FIN)
    def is_data(self): return bool(self.flags & FLAG_DATA)

    def __repr__(self):
        return f"Packet(seq={self.seq}, ack={self.ack}, flags={self.flags:08b}, len={len(self.payload)})"
