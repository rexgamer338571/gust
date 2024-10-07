import asyncio
import socket

from entity import tracker
from util.buf import PacketByteBuf


class PlayerByteBuf(PacketByteBuf):
    def __init__(self, sock: socket.socket):
        super().__init__(bytearray())
        self.sock = sock

    async def send(self):
        await asyncio.get_event_loop().sock_sendall(self.sock, self.get_data())
        self.flush()


class Player:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buffer = PlayerByteBuf(self.sock)
        self.entity_id = tracker.next_entity_id()
        self.last_keepalive = 0

