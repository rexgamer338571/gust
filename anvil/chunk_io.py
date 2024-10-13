import json
import math
import os
import struct
import zlib
from io import BytesIO
from typing import BinaryIO

import nbtlib
from nbtlib import Compound

from util import var
from util.buf import PacketByteBuf
from util.debug_packet import debug


class Util:
    path = os.getcwd() + ("/.." if os.getcwd().endswith("anvil") else "") + "/datagen/block/blocks.json"
    blocks_dict = json.loads(open(path, "r").read())

    @staticmethod
    def get_palette_id(root: nbtlib.List[nbtlib.Compound], block_state: str) -> int:
        index = 0
        for palette in root:
            if palette["Name"] == block_state:
                return index

            index += 1

        return -1

    @staticmethod
    def get_bpe(longs: int) -> int:
        bpe = round(64 / round(4096 / longs))
        return max(4, bpe)

    @staticmethod
    def get_block_count(air_palette: int, bpe: int, data: nbtlib.List[nbtlib.Long]) -> int:
        i: list[int] = []

        for long_value in data:
            bits = 0

            mask = (1 << bpe) - 1

            while (bits * bpe) < 64:
                entry = (long_value >> (bits * bpe)) & mask
                i.append(entry)
                bits += 1

        count = 0
        for entry in i:
            if entry != air_palette:
                count += 1

        return count


class ChunkIO:
    def __init__(self, bytez: bytes):
        self.buf = PacketByteBuf(bytez)

        self.data_length = self.buf.read_int()
        self.compression = self.buf.read_byte()
        self.data_compressed = self.buf.read_bytes(self.data_length)

    def get_decompressed_nbt(self) -> nbtlib.Compound:
        if self.compression != 2:
            print("Unsupported compression:", self.compression)
            return Compound()

        decompressed_bytes = zlib.decompress(self.data_compressed)

        bytes_io = BytesIO(decompressed_bytes)
        compound: nbtlib.Compound = nbtlib.File.from_fileobj(bytes_io)

        return compound


class ReadyChunk:
    def __init__(self, root: nbtlib.Compound):
        self.root = root

    @staticmethod
    def encode_varint(value: int) -> bytes:
        output = bytearray()

        while True:
            temp = value & 0b01111111
            value >>= 7

            if value:
                output.append(temp | 0b10000000)
            else:
                output.append(temp)
                break

        return bytes(output)

    def init(self) -> PacketByteBuf:
        packet = PacketByteBuf.empty()
        heightmaps_compound: nbtlib.Compound = self.root["Heightmaps"]
        heightmaps = BytesIO()

        heightmaps_compound.write(heightmaps)

        # print("Heightmaps", heightmaps.getvalue())

        chunk_sections_nbt: nbtlib.List[nbtlib.Compound] = self.root["sections"]

        data_array = PacketByteBuf.empty()

        # data array has:
        #

        for section_tag in chunk_sections_nbt:
            block_states: nbtlib.Compound = section_tag["block_states"]

            try:
                data_tag: nbtlib.List[nbtlib.Long] = block_states["data"]
            except KeyError:
                # single valued palette

                print("single valued")
                states = Util.blocks_dict[block_states["palette"][0]["Name"]]["states"]

                for state in states:
                    if not (state["default"]):
                        continue

                    data_array.write_varint(state["id"])

                continue

            air_palette_id = Util.get_palette_id(block_states["palette"], "minecraft:air")
            bpe = Util.get_bpe(len(data_tag))

            block_count = Util.get_block_count(air_palette_id, bpe, data_tag)

            data_array.write_short(block_count)  # block count in section

            # write paletted container

            data_array.write_bytes(struct.pack("B", bpe))  # bytes per entry as unsigned byte

            if bpe < 15:
                # indirect palette

                print("indirect")

                palette_tag: nbtlib.List[nbtlib.Compound] = block_states["palette"]
                data_array.write_varint(len(palette_tag))  # number of entries in the container

                for entry in palette_tag:
                    for state in Util.blocks_dict[entry["Name"]]["states"]:
                        try:
                            if not (state["default"]):
                                continue
                        except KeyError:
                            pass

                        data_array.write_varint(state["id"])

            else:
                print("direct")

            real_data_array = PacketByteBuf.empty()

            for long_value in data_tag:
                real_data_array.write_bytes(long_value.to_bytes(8, signed=True))

            vint = var.pack_varint(len(real_data_array.get_data()))
            print("vint:", vint)

            data_array.write_bytes(vint)
            data_array.write_bytes(real_data_array.get_data())

        x: int = self.root["xPos"]
        z: int = self.root["zPos"]

        p = PacketByteBuf.empty()

        # p should have:
        # vint length
        # vint packet_id = 0x25
        # i32 chunk_x
        # i32 chunk_z
        # nbt_compound heightmaps
        # bytearray data_array

        p.write_varint(0x25)

        p.write_int(x)  # chunk x
        p.write_int(z)  # chunk z

        real_heightmaps = bytearray([0x0a]) + heightmaps.getvalue()

        p.write_bytes(real_heightmaps)

        print("Heightmaps", debug(real_heightmaps))

        p.write_bytes(data_array.get_data())
        # packet.write_bytes(bytearray([0x0a, 0x00]))  # heightmaps nbt

        packet.write_varint(len(p.get_data()))
        packet.write_bytes(p.get_data())
        return packet


class MCAIO:
    made_chunks: list[PacketByteBuf] = []

    def __init__(self, root_path: str):
        self.root_path = root_path

    @staticmethod
    def get_mca(x: int, z: int) -> tuple[int, int]:
        return math.floor(x / 32), math.floor(z / 32)

    @staticmethod
    def get_location_entry_offset(x: int, z: int) -> int:
        return (x % 32 + (z % 32) * 32) * 4

    @staticmethod
    def chunk_location(entry: int) -> tuple[int, int]:
        offset = (entry >> 8) & 0xFFFFFF
        size = entry & 0xFF

        return offset * 4096, size * 4096

    async def xz_to_io(self, x: int, z: int) -> ChunkIO:
        which_mca: tuple[int, int] = MCAIO.get_mca(x, z)
        whole_file_buf: PacketByteBuf = PacketByteBuf.of_file(f"{self.root_path}/r.{which_mca[0]}.{which_mca[1]}.mca")

        locations_table = whole_file_buf.read_bytes(4096)
        whole_file_buf.read_bytes(4096)

        location_entry_offset = MCAIO.get_location_entry_offset(x, z)

        location_entry = struct.unpack(">I", locations_table[location_entry_offset : location_entry_offset + 4])[0]

        entry_offset_and_size = MCAIO.chunk_location(location_entry)

        chunk_data = whole_file_buf.get_data()[entry_offset_and_size[0] : entry_offset_and_size[0] + entry_offset_and_size[1]]
        return ChunkIO(chunk_data)


async def make_chunks(root_dir: str) -> None:
    mca_io: MCAIO = MCAIO(root_dir)

    for x in range(-2, 2):
        for z in range(-2, 2):
            chunk_io = await mca_io.xz_to_io(x, z)
            ready = ReadyChunk(chunk_io.get_decompressed_nbt())
            init = ready.init()

            MCAIO.made_chunks.append(init)