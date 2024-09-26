import asyncio
import socket

from entity import tracker
from entity.player.player import Player
from entity.tracker import next_teleport_id
from network.packet import PacketInRaw, PacketIn, PacketOut
from util import state
from util.var import pack_string, unpack_varint_socket


class PacketInClientInformation(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.locale = raw.buffer.read_string()
        self.view_distance = int(raw.buffer.read_byte())
        self.chat_mode = int(raw.buffer.read_byte())
        self.chat_colors = bool(raw.buffer.read_byte())
        self.displayed_skin_parts = int(raw.buffer.read_byte())
        self.main_hand = int(raw.buffer.read_byte())
        self.enable_text_filtering = bool(raw.buffer.read_byte())
        self.allow_server_listings = bool(raw.buffer.read_byte())


class PacketInPluginMessage(PacketIn):
    def __init__(self, raw: PacketInRaw):
        self.channel = raw.buffer.read_string()
        self.data = raw.buffer.read_remaining()


class PacketOutPluginMessage(PacketOut):
    def __init__(self, channel: str, data: bytes):
        super().__init__(0x00)
        self.buffer.write_string(channel)
        self.buffer.write_bytes(data)


class PacketOutFeatureFlags(PacketOut):
    def __init__(self, *flags: str):
        super().__init__(0x08)
        self.buffer.write_varint(len(flags))

        for flag in flags:
            self.buffer.write_string(flag)


class PacketOutRegistryData(PacketOut):
    def __init__(self):
        super().__init__(0x05)
        with open("datagen\\1.20.2.nbt", "rb") as a:
            self.buffer.write_bytes(a.read())


class PacketOutFinishConfiguration(PacketOut):
    def __init__(self):
        super().__init__(0x02)


class PacketOutLoginPlay(PacketOut):
    def __init__(self):
        super().__init__(0x29)
        self.buffer.write_int(tracker.next_entity_id())
        self.buffer.write_bool(True)

        # self.buffer.write_varint(1)

        self.buffer.write_varint(1)
        self.buffer.write_string("minecraft:overworld")

        self.buffer.write_varint(2)
        self.buffer.write_varint(2)
        self.buffer.write_varint(5)
        self.buffer.write_bool(False)
        self.buffer.write_bool(True)
        self.buffer.write_bool(False)
        self.buffer.write_string("minecraft:overworld")
        self.buffer.write_string("minecraft:overworld")
        self.buffer.write_bytes(bytearray([0x5f, 0xec, 0xeb, 0x66, 0xff, 0xc8, 0x6f, 0x38]))
        self.buffer.write_bytes(bytearray([1]))
        self.buffer.write_bytes(bytearray([2]))
        self.buffer.write_bool(False)
        self.buffer.write_bool(False)
        self.buffer.write_bool(False)
        self.buffer.write_varint(0)


class PacketOutChangeDifficulty(PacketOut):
    def __init__(self, difficulty: int, locked: bool):
        super().__init__(0x0B)
        self.buffer.write_bytes(difficulty.to_bytes(1))
        self.buffer.write_bool(locked)


class PacketOutPlayerAbilities(PacketOut):
    def __init__(self, invulnerable: bool, flying: bool, allow_flying: bool, creative_mode: bool,
                 flying_speed: float, fov_modifier: float):
        super().__init__(0x36)
        bitmask = 0
        if invulnerable:
            bitmask |= 0x01
        if flying:
            bitmask |= 0x02
        if allow_flying:
            bitmask |= 0x04
        if creative_mode:
            bitmask |= 0x08

        self.buffer.write_bytes(bytearray([bitmask]))
        self.buffer.write_float(flying_speed)
        self.buffer.write_float(fov_modifier)


class PacketOutSynchronizePlayerPosition(PacketOut):
    BITMASK_X = 0x01
    BITMASK_Y = 0x02
    BITMASK_Z = 0x04
    BITMASK_Y_ROT = 0x08
    BITMASK_X_ROT = 0x10

    def __init__(self, x: float, y: float, z: float, yaw: float, pitch: float, bitmask: int):
        super().__init__(0x3E)
        self.buffer.write_double(x)
        self.buffer.write_double(y)
        self.buffer.write_double(z)
        self.buffer.write_float(yaw)
        self.buffer.write_float(pitch)
        self.buffer.write_byte(bitmask)
        self.buffer.write_varint(next_teleport_id())


async def _brand_response(client: Player):
    # if new_packet.channel == "minecraft:brand":
    print("Responding with brand response")

    response = PacketOutPluginMessage("minecraft:brand", pack_string("Gust"))
    await response.send(client)

    print("Sending feature flags")
    ff = PacketOutFeatureFlags("vanilla")

    await ff.send(client)
    print("Sending registry data")

    rd = PacketOutRegistryData()
    await rd.send(client)

    print("Sending finish configuration")

    fc = PacketOutFinishConfiguration()
    await fc.send(client)


async def on_client_information(client: Player, packet: PacketInRaw):
    print("Client information")

    new_packet = PacketInClientInformation(packet)

    print(f"Locale: {new_packet.locale}, View distance: {new_packet.view_distance}, Chat mode: {new_packet.chat_mode}, "
          f"Chat colors: {new_packet.chat_colors}, Skin parts: {new_packet.displayed_skin_parts}, Main hand: {new_packet.main_hand}, "
          f"Text filtering: {new_packet.enable_text_filtering}, Server listing: {new_packet.allow_server_listings}")

    await _brand_response(client)


async def on_plugin_message(client: Player, packet: PacketInRaw):
    print("Plugin message")

    new_packet = PacketInPluginMessage(packet)

    print(f"Channel: {new_packet.channel}, Data: {new_packet.data}")


async def on_ack_finish_configuration(client: Player, packet: PacketInRaw):
    print("Acknowledged finish configuration")
    print("Sending login (play)")

    lp = PacketOutLoginPlay()
    await lp.send(client)

    state.set_state(state.PLAY)
    print("Setting state to PLAY")

    # difficulty = PacketOutChangeDifficulty(0, True)
    # abilities = PacketOutPlayerAbilities(False, False, False, True, 0.0, 0.0)
    sync_pos = PacketOutSynchronizePlayerPosition(10.0, 300.0, 10.0, 50.0, 50.0, 0)
    # await difficulty.send(client)
    # await abilities.send(client)
    await sync_pos.send(client)
