import json
import socket

from entity.player.player import Player
from network.packet import PacketInRaw, PacketOut, PacketIn


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

    response_json = json.dumps({
        "version": {
            "name": "1.20.4",
            "protocol": 765
        },
        "players": {
            "max": 69,
            "online": 0,
            "sample": [
                {
                    "name": "NG5M",
                    "id": "eecec455-8813-4271-8223-4b28d98bc706"
                }
            ]
        },
        "description": {
            "text": "A Gust server"
        },
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
