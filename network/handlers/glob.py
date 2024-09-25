from events.event_dispatcher import register, PacketInEvent, register_packet, TeleportConfirmEvent
from network.handlers.configuration import *
from network.handlers.handshake import *
from network.handlers.login import *
from network.handlers.play import *
from network.handlers.status import *
from util.state import get_state, HANDSHAKE, LOGIN, CONFIGURATION, STATUS, PLAY
from world.chunk import ChunkSection, PalettedContainer


async def global_handle_packet(event: PacketInEvent):
    packet = event.packet

    print("Serverbound packet, connection state:", get_state())
    print("Data:", packet.packet_length, packet.packet_id, packet.buffer)
    print("Calling packet-specific handler")

    await event.call_packet_listener()


async def global_teleport_confirm(event: TeleportConfirmEvent):
    if event.teleport_id != tracker.teleport_id:
        print("Invalid teleport ID")
        return

    response = PacketOutGameEvent(PacketOutGameEvent.START_WAITING_FOR_LEVEL_CHUNKS, 0.0)
    await response.send(event.client)

    response2 = PacketOutSetCenterChunk(0, 0)
    await response2.send(event.client)

    for x in range(-2, 2):
        for z in range(-2, 2):
            containers: list[PalettedContainer] = [PalettedContainer(0, bytearray([0xa]))]
            biomes: list[PalettedContainer] = [PalettedContainer(0, bytearray([0xa]))]

            # for i in range(4096):
            #     container = PalettedContainer(0, bytearray([0xa]))
            #     containers.append(container)

            chunk_packet = PacketOutChunkData(x, z, bytearray([0x0a, 0x00]), ChunkSection(4096, containers, biomes).write())
            await chunk_packet.send(event.client)



async def register_global():
    await register(PacketInEvent, global_handle_packet)
    await register(TeleportConfirmEvent, global_teleport_confirm)


async def register_packets():
    register_packet(HANDSHAKE, 0x00, on_handshake)

    register_packet(STATUS, 0x00, on_status_request)

    register_packet(LOGIN, 0x00, on_login_start)
    register_packet(LOGIN, 0x03, on_login_ack)

    register_packet(CONFIGURATION, 0x00, on_client_information)
    register_packet(CONFIGURATION, 0x01, on_plugin_message)
    register_packet(CONFIGURATION, 0x02, on_ack_finish_configuration)

    register_packet(PLAY, 0x00, on_confirm_teleport)
    register_packet(PLAY, 0x10, on_plugin_message_play)
    register_packet(PLAY, 0x17, on_player_position)
    register_packet(PLAY, 0x18, on_player_position_and_rotation)
    register_packet(PLAY, 0x19, on_player_rotation)


async def register_all():
    await register_global()

    await register_packets()
