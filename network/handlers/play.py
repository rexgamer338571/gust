import socket

from nbt.nbt import TAG_Compound

from entity.player.player import Player
from events import event_dispatcher
from network.handlers.configuration import PacketInPluginMessage
from network.packet import PacketInRaw, PacketIn, PacketOut


class PacketInConfirmTeleport(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.teleport_id = raw.buffer.read_varint()


class PacketInPlayerPositionAndRotation(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.absolute_x = raw.buffer.read_double()
        self.absolute_feet_y = raw.buffer.read_double()
        self.absolute_z = raw.buffer.read_double()
        self.yaw = raw.buffer.read_float()
        self.pitch = raw.buffer.read_float()
        self.on_ground = raw.buffer.read_bool()


class PacketInPlayerRotation(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.yaw = raw.buffer.read_float()
        self.pitch = raw.buffer.read_float()
        self.on_ground = raw.buffer.read_bool()


class PacketInPlayerPosition(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.absolute_x = raw.buffer.read_double()
        self.absolute_feet_y = raw.buffer.read_double()
        self.absolute_z = raw.buffer.read_double()
        self.on_ground = raw.buffer.read_bool()


class PacketOutGameEvent(PacketOut):
    NO_RESPAWN_BLOCK_AVAILABLE = 0
    END_RAINING = 1
    BEGIN_RAINING = 2
    CHANGE_GAME_MODE = 3
    WIN_GAME = 4
    DEMO_EVENT = 5
    ARROW_HIT_PLAYER = 6
    RAIN_LEVEL_CHANGE = 7
    THUNDER_LEVEL_CHANGE = 8
    PLAY_PUFFERFISH_STING_SOUND = 9
    PLAY_ELDER_GUARDIAN_EFFECT = 10
    ENABLE_RESPAWN_SCREEN = 11
    LIMITED_CRAFTING = 12
    START_WAITING_FOR_LEVEL_CHUNKS = 13

    def __init__(self, event: int, value: float):
        super().__init__(0x20)
        self.buffer.write_byte(event)
        self.buffer.write_float(value)


class PacketOutSetCenterChunk(PacketOut):
    def __init__(self, x: int, z: int):
        super().__init__(0x52)
        self.buffer.write_varint(x)
        self.buffer.write_varint(z)


class PacketOutChunkData(PacketOut):
    def __init__(self, x: int, z: int, heightmaps: TAG_Compound, data: bytes):
        super().__init__(0x25)
        self.buffer.write_int(x)
        self.buffer.write_int(z)
        self.buffer.write_compound(heightmaps)
        self.buffer.write_bytes(data)


async def on_confirm_teleport(client: Player, packet: PacketInRaw):
    print("Teleport confirm")
    new_packet = PacketInConfirmTeleport(packet)
    print(f"Teleport ID: {new_packet.teleport_id.value}")

    await event_dispatcher.fire(event_dispatcher.TeleportConfirmEvent(client, new_packet.teleport_id.value))


async def on_plugin_message_play(client: Player, packet: PacketInRaw):
    print("Plugin message")

    new_packet = PacketInPluginMessage(packet)

    print(f"Channel: {new_packet.channel}, Data: {new_packet.data}")


async def on_player_position(client: Player, packet: PacketInRaw):
    print("Player position")

    new_packet = PacketInPlayerPosition(packet)

    print(f"x: {new_packet.absolute_x} y: {new_packet.absolute_feet_y} z: {new_packet.absolute_z} on_ground: {new_packet.on_ground}")


async def on_player_position_and_rotation(client: Player, packet: PacketInRaw):
    print("Position and rotation")

    new_packet = PacketInPlayerPositionAndRotation(packet)

    print(f"x: {new_packet.absolute_x} feet y: {new_packet.absolute_feet_y} z: {new_packet.absolute_z} "
          f"yaw: {new_packet.yaw} pitch: {new_packet.pitch}")


async def on_player_rotation(client: Player, packet: PacketInRaw):
    print("Player rotation")

    new_packet = PacketInPlayerRotation(packet)

    print(f"yaw: {new_packet.yaw} pitch: {new_packet.pitch} on_ground: {new_packet.on_ground}")
