import asyncio
import socket
import struct

from entity.player.player import Player
from util import var
from util.buf import PacketByteBuf


class PacketIn:
    pass


class PacketOut:
    def __init__(self, packet_id: int):
        self.buffer: PacketByteBuf = PacketByteBuf(bytearray())
        self.packet_id = packet_id

    async def write(self):
        self.buffer.write_at_front(var.pack_varint(self.packet_id))
        self.buffer.write_at_front(var.pack_varint(len(self.buffer.get_data())))

    async def send(self, client: Player):
        await self.write()
        print(f"Sending: {self.buffer.get_data()}")
        client.buffer.set_data(self.buffer.get_data())
        await client.buffer.send()

    pass


class PacketInRaw(PacketIn):
    def __init__(self, packet_length: int, packet_id: int, packet_data: bytes):
        self.packet_length = packet_length
        self.packet_id = packet_id
        self.buffer: PacketByteBuf = PacketByteBuf(packet_data)
