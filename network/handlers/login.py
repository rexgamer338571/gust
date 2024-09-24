import socket

from entity.player.player import Player
from network.packet import PacketInRaw, PacketIn, PacketOut, PacketByteBuf
from util import state


class PacketInLoginStart(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.username = raw.buffer.read_string()
        self.uuid_bytes = raw.buffer.read_bytes(16)


class PacketOutLoginSuccess(PacketOut):
    def __init__(self, login_start: PacketInLoginStart):
        super().__init__(0x02)
        self.buffer.write_bytes(login_start.uuid_bytes)
        self.buffer.write_string(login_start.username)
        self.buffer.write_varint(0)


async def on_login_start(client: Player, packet: PacketInRaw):
    print("Login start")

    new_packet = PacketInLoginStart(packet)

    print(f"Player trying login: {new_packet.username} with uuid {new_packet.uuid_bytes}")
    print("Responding with login success")

    response = PacketOutLoginSuccess(new_packet)
    await response.send(client)


async def on_login_ack(client: Player, packet: PacketInRaw):
    print("Login acknowledged, switching state to CONFIGURATION")

    state.set_state(state.CONFIGURATION)
