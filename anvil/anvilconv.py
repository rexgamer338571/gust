import io
import json
import os
import struct
import zlib

import nbtlib

from util.buf import PacketByteBuf
from util.misc import get_root_dir


def chunk_location(i: int):
    offset = ((i >> 8) & 0xFFFFFF)
    size = i & 0xFF

    return offset * 4096, size * 4096


def cleanup(path: str):
    for a, b, c in os.walk(path):
        for f in c:
            os.remove(path + "\\" + f)


def convert(path: str, out: str) -> None:
    cleanup(out)

    buf = PacketByteBuf.of_file(path)

    locations_table = PacketByteBuf(buf.read_bytes(4096))
    timestamps_table = buf.read_bytes(4096)

    for i in range(1024):
        entry = locations_table.read_int()

        loc = chunk_location(entry)

        chunk_data = PacketByteBuf(buf.get_data()[loc[0]:loc[0] + loc[1]])

        # print(chunk_data)

        try:
            supposed_length = chunk_data.read_int()  # supposed length
        except IndexError:
            continue

        compression = chunk_data.read_byte()

        print("compression", compression)

        if compression != 2:
            print("invalid compression", compression)
            continue

        decompressed = zlib.decompress(chunk_data.read_bytes(supposed_length))

        io_ = io.BytesIO(decompressed)

        parsed: nbtlib.Compound = nbtlib.File.from_fileobj(io_)

        chunk_x = parsed["xPos"].unpack()
        chunk_z = parsed["zPos"].unpack()

        with open(out + "\\" + str(chunk_x) + "_" + str(chunk_z) + ".nbt", "wb") as f:
            f.write(decompressed)

        continue


out = "C:\\Users\\wojci\\Gust\\anvil\\test1"


def get_palette_id(root: nbtlib.List[nbtlib.Compound], block_state: str) -> int:
    index = 0
    for palette in root:
        if palette["Name"] == block_state:
            return index

        index += 1

    return -1


def get_bpe(longs: int) -> int:
    bpe = round(64 / round(4096 / longs))
    return max(4, bpe)


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


path = os.getcwd() + ("\\.." if os.getcwd().endswith("anvil") else "") + "\\datagen\\block\\blocks.json"
blocks_dict = json.loads(open(path, "r").read())


def load_chunk(x: int, z: int) -> bytes:
    name = out + "\\" + str(x) + "_" + str(z) + ".nbt"
    print(name)
    if not os.path.isfile(name):
        return b''

    root: nbtlib.Compound = nbtlib.load(name)

    packet = PacketByteBuf.empty()
    heightmaps_compound: nbtlib.Compound = root["Heightmaps"]
    heightmaps = io.BytesIO()

    heightmaps_compound.write(heightmaps)

    print("Heightmaps", heightmaps.getvalue())

    chunk_sections_nbt: nbtlib.List[nbtlib.Compound] = root["sections"]

    data_array = PacketByteBuf.empty()

    for section_tag in chunk_sections_nbt:
        block_states: nbtlib.Compound = section_tag["block_states"]

        try:
            data_tag: nbtlib.List[nbtlib.Long] = block_states["data"]
        except KeyError:
            # single valued palette

            print("single valued")
            states = blocks_dict[block_states["palette"][0]["Name"]]["states"]

            for state in states:
                if not (state["default"]):
                    continue

                data_array.write_varint(state["id"])

            continue

        air_palette_id = get_palette_id(block_states["palette"], "minecraft:air")
        bpe = get_bpe(len(data_tag))

        block_count = get_block_count(air_palette_id, bpe, data_tag)

        data_array.write_short(block_count)        # block count in section

        # write paletted container

        data_array.write_bytes(struct.pack("B", bpe))        # bytes per entry as unsigned byte

        if bpe < 15:
            # indirect palette

            print("indirect")

            palette_tag: nbtlib.List[nbtlib.Compound] = block_states["palette"]
            data_array.write_varint(len(palette_tag))                               # number of entries in the container

            for entry in palette_tag:
                for state in blocks_dict[entry["Name"]]["states"]:
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

        data_array.write_varint(len(real_data_array.get_data()))
        data_array.write_bytes(real_data_array.get_data())

    packet.write_int(x)  # chunk x
    packet.write_int(z)  # chunk z

    real_heightmaps = bytearray([0x0a]) + heightmaps.getvalue() + bytearray([0x00])

    packet.write_bytes(real_heightmaps)
    # packet.write_bytes(bytearray([0x0a, 0x00]))  # heightmaps nbt

    return packet.get_data()


if __name__ == "__main__":
    chunk = load_chunk(0, 0)
    # load_chunk(0, 0)
    # convert(
    #     "C:\\Users\\wojci\\Downloads\\mmc-develop-win32\\MultiMC\\instances\\1.20.4 fabric\\.minecraft\\saves\\New World\\region\\r.0.0.mca",
    #     out)
