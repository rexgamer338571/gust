import socket

from entity.player.player import Player
from network.packet import PacketIn, PacketInRaw
import util.state


class PacketInHandshake(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.protocol_version = raw.buffer.read_varint()
        self.address = raw.buffer.read_string()
        self.next_state = raw.buffer.data[-1]


async def on_handshake(c: Player, p: PacketInRaw):
    new_packet = PacketInHandshake(p)

    print("Handshake from: ", c.sock.getpeername())
    print(new_packet.protocol_version.value, new_packet.address)
    print("New state: ", new_packet.next_state)
    util.state.set_state(new_packet.next_state)
