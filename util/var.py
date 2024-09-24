import asyncio
import struct
import socket


class SkinParts:
    def __init__(self, cape: bool, jacket: bool, left_sleeve: bool, right_sleeve: bool, left_pants: bool,
                 right_pants: bool, hat: bool):
        self.cape = cape
        self.jacket = jacket
        self.left_sleeve = left_sleeve
        self.right_sleeve = right_sleeve
        self.left_pants = left_pants
        self.right_pants = right_pants
        self.hat = hat


def pack_varint(val: int):
    total = b''
    if val < 0:
        val = (1 << 32) + val
    while val >= 0x80:
        bits = val & 0x7F
        val >>= 7
        total += struct.pack('B', (0x80 | bits))
    bits = val & 0x7F
    total += struct.pack('B', bits)
    return total


async def unpack_varint_socket(sock: socket.socket) -> int:
    total = 0
    shift = 0
    val = 0x80
    while val & 0x80:
        try:
            val = struct.unpack('B', await asyncio.get_event_loop().sock_recv(sock, 1))[0]
        except struct.error:
            print("Connection finished")
            exit(0)

        total |= ((val & 0x7F) << shift)
        shift += 7
    if total & (1 << 31):
        total = total - (1 << 32)
    return total


def unpack_varint(buff) -> tuple:
    total = 0
    shift = 0
    b = 0
    val = 0x80
    while val & 0x80:
        val = buff[b]
        b += 1
        total |= ((val & 0x7F) << shift)
        shift += 7
    if total & (1 << 31):
        total = total - (1 << 32)
    return total, b


def unpack_string(buff) -> tuple:
    length, _ = unpack_varint(buff)
    return buff[1:1 + length], length


def pack_string(s: str) -> bytes:
    return pack_varint(len(s)) + bytes(s, 'utf-8')


def unpack_bool(byte) -> bool:
    if byte == 0x00:
        return False
    elif byte == 0x01:
        return True


def pack_bool(b: bool) -> bytes:
    if b:
        return b'\x01'
    else:
        return b'\x00'


def unpack_skin_parts(bitmask) -> SkinParts:
    return SkinParts(
        (bitmask & 0x01) != 0,
        (bitmask & 0x02) != 0,
        (bitmask & 0x04) != 0,
        (bitmask & 0x08) != 0,
        (bitmask & 0x10) != 0,
        (bitmask & 0x20) != 0,
        (bitmask & 0x40) != 0
    )
