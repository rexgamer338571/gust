import json
import socket

from entity.player.player import Player
from network.packet import PacketInRaw, PacketOut, PacketIn
from util.misc import get_server


class PacketOutStatusResponse(PacketOut):
    def __init__(self, response: str):
        super().__init__(0x00)
        self.buffer.write_string(response)


class PacketInPingRequest(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.payload = raw.buffer.read_bytes(8)


class PacketOutPongResponse(PacketOut):
    def __init__(self, request: PacketInPingRequest):
        super().__init__(0x01)
        self.buffer.write_bytes(request.payload)


async def on_status_request(client: Player, packet: PacketInRaw):
    print("Status request")

    server_handle = get_server()

    response_json = json.dumps({
        "version": {
            "name": server_handle.settings.version,
            "protocol": server_handle.settings.protocol_version
        },
        "players": {
            "max": server_handle.settings.max_online,
            "online": server_handle.online,
            "sample": []
        },
        "description": server_handle.settings.motd,
        "enforcesSecureChat": False,
        "previewsChat": False
    })

    response = PacketOutStatusResponse(response_json)
    await response.send(client)


async def on_ping_request(client: Player, packet: PacketInRaw):
    print("Ping request")
    new_packet = PacketInPingRequest(packet)
    print("Payload:", new_packet.payload)

    response = PacketOutPongResponse(new_packet)
    await response.send(client)
