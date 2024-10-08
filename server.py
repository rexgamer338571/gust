import asyncio
import socket
from typing import Any

from entity.player.player import Player
from events.event_dispatcher import PacketInEvent, fire
from network.handlers.glob import register_all
from network.packet import PacketInRaw
from ticker import ticker
from util.buf import PacketByteBuf


class ServerSettings:
    def __init__(self, max_online: int, motd: dict[str, Any], version: str, protocol_version: int):
        self.max_online = max_online
        self.motd = motd
        self.version = version
        self.protocol_version = protocol_version


class Server:
    def __init__(self, addr: tuple[str, int], settings: ServerSettings):
        self.addr = addr
        self.settings = settings

        self.online = 0

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        await register_all()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.addr)
        server.listen(8)
        server.setblocking(True)

        loop = asyncio.get_event_loop()

        while True:
            client, _ = await loop.sock_accept(server)
            await loop.create_task(self.handle_connection(client))

    async def handle_connection(self, client: socket.socket):
        try:
            while True:
                player: Player = Player(client)
                ticker.players.append(player)

                try:
                    d = PacketByteBuf(await asyncio.get_event_loop().sock_recv(client, 1024))
                    packet_length = d.read_varint().value
                    packet_id = d.read_varint().value
                    packet_data = d.read_remaining()
                except asyncio.TimeoutError:
                    print("Connection timed out")
                    return
                except SystemExit:
                    return

                await fire(PacketInEvent(player, PacketInRaw(packet_length, packet_id, packet_data)))

        finally:
            client.close()
