import io
import random
import socket

import nbtlib
from nbt.nbt import TAG_Compound

from anvil.anvilconv import load_chunk
from anvil.anvilloader import AnvilLoader
from entity.player.player import Player
from events import event_dispatcher
from network.handlers.configuration import PacketInPluginMessage, PacketInClientInformation
from network.packet import PacketInRaw, PacketIn, PacketOut
from util.bitset import BitSet
from world.chunk import which_mca


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


class PacketInOnGround(PacketIn):
    def __init__(self, raw: PacketInRaw):
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
    def __init__(self, x: int, z: int):
        super().__init__(0x25)

        self.buffer.write_int(x)
        self.buffer.write_int(z)
        chunk_data = load_chunk(x, z)

        if chunk_data == b'':
            self.fail = True
            return
        else:
            self.fail = False

        self.buffer.write_bytes(chunk_data)     # heightmaps, size of data, data array

        self.buffer.write_varint(0)             # block entity count

        sky_light_mask = int("0b" + ("1"*26), 2)
        block_light_mask = int("0b" + ("1"*26), 2)

        empty_sky_light_mask = int("0b" + ("0"*26), 2)
        empty_block_light_mask = int("0b" + ("0"*26), 2)

        self.buffer.write_bytes(sky_light_mask.to_bytes(4))
        self.buffer.write_bytes(block_light_mask.to_bytes(4))
        self.buffer.write_bytes(empty_sky_light_mask.to_bytes(4))
        self.buffer.write_bytes(empty_block_light_mask.to_bytes(4))

        self.buffer.write_varint(26)            # same number as bits in skylight mask
        self.buffer.write_varint(2048)          # length of the following array
        self.buffer.write_bytes(int("0b" + ("1111"*26), 2).to_bytes(2048))      # the array

        self.buffer.write_varint(26)  # same number as bits in skylight mask
        self.buffer.write_varint(2048)  # length of the following array
        self.buffer.write_bytes(int("0b" + ("1111" * 26), 2).to_bytes(2048))  # the array

        # self.buffer.write_int(x)
        # self.buffer.write_int(z)

        # mca = which_mca(x, z)
        # anvil_loader = AnvilLoader(f"C:\\Users\\wojci\\AppData\\Roaming\\.minecraft\\saves\\New World (8)\\region\\r.{int(mca[0])}.{int(mca[1])}.mca")
        # preloaded_mca = anvil_loader.load()
        # loaded_mca = preloaded_mca.load()
        #
        # self.buffer.write_bytes(heightmaps)
        # self.buffer.write_varint(len(data))

        # for chunk in loaded_mca:
        #     # if chunk.compression_type == 2:         # zlib
        #     if chunk.failed:
        #         continue
        #
        #     root_chunk: nbtlib.Compound = chunk.decompress_zlib()
        #     maps_compound: nbtlib.Compound = root_chunk["Heightmaps"]
        #     _ = io.BytesIO()
        #     maps_compound.write(_)
        #     print(_.getvalue())
        #     self.buffer.write_bytes(bytearray([0xa]) + _.getvalue() + bytearray([0]))
        #
        # self.buffer.write_varint(0)
        #
        # # sky_light_mask = BitSet(1, [0b1 for i in range(24 + 2)])
        # # block_light_mask = BitSet(1, [0b1 for i in range(24 + 2)])
        # # empty_sky_light_mask = BitSet(1, [0b0 for i in range(24 + 2)])
        # # empty_block_light_mask = BitSet(1, [0b0 for i in range(24 + 2)])
        #
        # # self.buffer.write_bytes(sky_light_mask.get())
        # # self.buffer.write_bytes(block_light_mask.get())
        # # self.buffer.write_bytes(empty_sky_light_mask.get())
        # # self.buffer.write_bytes(empty_block_light_mask.get())

        # self.buffer.write_varint(1)
        # self.buffer.write_bytes(0b11111111_11111111_11111111_11.to_bytes(length=4, byteorder='big'))
        # self.buffer.write_varint(1)
        # self.buffer.write_bytes(0b11111111111111111111111111.to_bytes(length=4, byteorder='big'))
        # self.buffer.write_varint(0)
        # self.buffer.write_varint(0)
        #
        # self.buffer.write_varint(24 + 2)
        #
        # self.buffer.write_varint(2048)
        # self.buffer.write_bytes(bytearray([0b10011001 for i in range(2048)]))
        #
        # self.buffer.write_varint(2048)
        # self.buffer.write_bytes(bytearray([0b10011001 for i in range(2048)]))
        #
        # self.buffer.write_varint(0)
        # self.buffer.write_varint(0)
        # self.buffer.write_varint(0)
        #
        # self.buffer.write_varint(0)
        # self.buffer.write_varint(0)


class PacketPlayOutKeepAlive(PacketOut):
    def __init__(self):
        super().__init__(0x24)
        self.buffer.write_long(random.randint(0, 9223372036854775806))


async def on_confirm_teleport(client: Player, packet: PacketInRaw):
    print("Teleport confirm")
    new_packet = PacketInConfirmTeleport(packet)
    print(f"Teleport ID: {new_packet.teleport_id.value}")

    await event_dispatcher.fire(event_dispatcher.TeleportConfirmEvent(client, new_packet.teleport_id.value))


async def on_client_information_play(client: Player, packet: PacketInRaw):
    print("Client information")

    new_packet = PacketInClientInformation(packet)

    print(f"Locale: {new_packet.locale}, View distance: {new_packet.view_distance}, Chat mode: {new_packet.chat_mode}, "
          f"Chat colors: {new_packet.chat_colors}, Skin parts: {new_packet.displayed_skin_parts}, Main hand: {new_packet.main_hand}, "
          f"Text filtering: {new_packet.enable_text_filtering}, Server listing: {new_packet.allow_server_listings}")


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


async def on_player_on_ground(client: Player, packet: PacketInRaw):
    print("On ground")

    new_packet = PacketInOnGround(packet)

    print("Is on ground:", new_packet.on_ground)