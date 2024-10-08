import io
import os
import zlib

import nbtlib

from util.buf import PacketByteBuf


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

        print("chunk", i)
        print(loc)

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


def load_chunk(x: int, z: int):
    name = out + "\\" + str(x) + "_" + str(z) + ".nbt"
    if not os.path.isfile(name):
        return

    root: nbtlib.Compound = nbtlib.load(name)

    packet = PacketByteBuf.empty()
    heightmaps_compound: nbtlib.Compound = root["Heightmaps"]
    heightmaps = io.BytesIO()

    heightmaps_compound.write(heightmaps)

    chunk_sections_nbt: nbtlib.List = root["sections"]

    data_array = PacketByteBuf.empty()

    data_array.write_short(32767)

    packet.write_int(x)  # chunk x
    packet.write_int(z)  # chunk z

    packet.write_bytes(heightmaps.getvalue())  # heightmaps nbt


if __name__ == "__main__":
    convert(
        "C:\\Users\\wojci\\Downloads\\mmc-develop-win32\\MultiMC\\instances\\1.20.4 fabric\\.minecraft\\saves\\New World\\region\\r.0.0.mca",
        out)
