import io
import struct

from nbt.nbt import TAG_Compound


class VarNum:
    def __init__(self, value: int, byte_length: int):
        self.value = value
        self.byte_length = byte_length


class PacketByteBuf:
    def __init__(self, data: bytes):
        self.data = data
        self.index = 0

    def __str__(self):
        return str(self.data)

    def flush(self):
        self.index = 0
        self.set_data(bytearray())

    def set_data(self, bytez: bytes):
        self.data = bytez

    def get_data(self) -> bytes:
        return self.data

    def read_byte(self) -> int:
        b = self.data[self.index]
        self.index += 1
        return b

    def write_byte(self, b):
        self.write_bytes(bytearray([b]))

    def write_bytes(self, bytez: bytes):
        self.data += bytez

    def write_float(self, f: float):
        self.write_bytes(struct.pack('>f', f))

    def read_float(self) -> float:
        return struct.unpack('>f', self.read_bytes(4))[0]

    def write_double(self, d: float):
        self.write_bytes(struct.pack('d', d))

    def read_double(self) -> float:
        return struct.unpack('d', self.read_bytes(8))[0]

    def write_at_front(self, bytez: bytes):
        self.set_data(bytez + self.data)

    def read_bytes(self, count: int) -> bytearray:
        li = bytearray()
        for i in range(count):
            li.append(self.read_byte())

        return li

    def read_remaining(self) -> bytes:
        return self.get_data()[self.index:]

    def write_short(self, s: int):
        self.write_bytes(struct.pack('h', s))

    def write_int(self, i: int):
        self.write_bytes(struct.pack('>i', i))

    def write_long(self, l: int):
        self.write_bytes(struct.pack('q', l))

    def write_bool(self, b: bool):
        self.write_bytes(struct.pack('?', b))

    def write_compound(self, c: TAG_Compound):
        buf = io.BytesIO()
        c._render_buffer(buf)
        self.write_bytes(buf.getvalue())

    def read_bool(self) -> bool:
        return struct.unpack('?', self.read_bytes(1))[0]

    def read_varint(self) -> VarNum:
        total = 0
        shift = 0
        b = self.index
        val = 0x80
        while val & 0x80:
            val = self.read_byte()
            total |= ((val & 0x7F) << shift)
            shift += 7

        if total & (1 << 31):
            total = total - (1 << 32)

        return VarNum(total, self.index - b)

    def write_varint(self, val: int):
        ret = b''
        if val < 0:
            val = (1 << 32) + val

        while val >= 0x80:
            bits = val & 0x7F
            val >>= 7
            ret += struct.pack('B', (0x80 | bits))

        bits = val & 0x7F
        ret += struct.pack('B', bits)

        self.write_bytes(ret)

    def read_string(self) -> str:
        length = self.read_varint()

        return self.read_bytes(length.value).decode("utf-8")

    def write_string(self, s: str):
        self.write_varint(len(s))
        self.write_bytes(bytes(s, 'utf-8'))