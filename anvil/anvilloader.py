import io
import zlib

import nbtlib
from nbt.nbt import *

from util.buf import PacketByteBuf


def pretty_tree(d, indent=0):
    for key, value in d.items():
        print(' ' * indent + str(key))
        if isinstance(value, dict):
            pretty_tree(value, indent + 4)
        else:
            print(' ' * (indent + 4) + str(value))


def chunk_location(l):
    offset = ((l >> 8) & 0xFFFFFF)
    size = l & 0xFF

    return offset * 4096, size * 4096


class Chunk:
    def __init__(self, mca: str, data: bytes):
        self.buf = PacketByteBuf(data)
        self.mca = mca

        # print("Chunk data", self.buf.get_data())
        if self.buf.get_data() == b'':
            self.failed = True
            return
        else:
            self.failed = False

        bytez = self.buf.read_bytes(4)

        # print(bytez)
        self.chunk_data_length = int.from_bytes(bytez)
        # print(self.chunk_data_length)
        self.compression_type = self.buf.read_byte()
        # print(self.compression_type)
        # except IndexError:
        #     pass

        # if self.compression_type == 2:
        #     root_compound: nbtlib.File = self.decompress_zlib()
        # print(pretty_tree(root_compound["Heightmaps"]))

    def decompress_zlib(self) -> nbtlib.File:
        decompressed = zlib.decompress(self.buf.read_bytes(self.chunk_data_length))
        _io = io.BytesIO()
        _io.write(decompressed)

        fn = self.mca.split("\\")[-1].strip(".mca") + ".gdc"
        with open(fn, "wb") as f:
            f.write(_io.getvalue())

        return nbtlib.load(fn)


class MCA:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> list[Chunk]:
        print("Loading MCA", self.path)
        file = open(self.path, "rb")
        buf = PacketByteBuf(file.read())

        locations_table = buf.read_bytes(4096)
        buf.read_bytes(4096)  # timestamps table

        ret = []
        for i in range(0, 4096):
            location = chunk_location(int.from_bytes(locations_table[i:i + 4]))
            chunk = Chunk(self.path, buf.get_data()[location[0]:location[0] + location[1]])
            ret.append(chunk)

        return ret

        # location = chunk_location(int.from_bytes(locations_table[0:4]))
        # print(location)
        # chunk = Chunk(self.path, buf.get_data()[location[0]:location[0] + location[1]])
        #
        # print(chunk)


class AnvilLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> MCA:
        loaded = False

        with open(self.path, "rb"):
            mca = MCA(self.path)
            return mca

        # for root, dirs, files in os.walk(self.path):
        #     for filename in files:
        #         if filename.endswith(".mca") and not loaded:
        #             mca = MCA(os.path.join(root, filename))
        #             mca.load()
        #             loaded = True


def sections_nbt_to_bytearray(sections_nbt: nbtlib.List) -> bytes:
    if sections_nbt.subtype != nbtlib.Compound:
        raise ValueError("Not a compound array")

    arr = bytearray()

    for i in sections_nbt:
        section_compound: nbtlib.Compound = i

        block_states: nbtlib.Compound = section_compound["block_states"]

        print(pretty_tree(section_compound))


# peter = AnvilLoader(
#     "C:\\Users\\wojci\\AppData\\Roaming\\.minecraft\\saves\\New World (8)\\region\\r.0.0.mca").load().load()[
#     0].decompress_zlib()["sections"]
#
# # sections_nbt_to_bytearray(peter)
# # sections_nbt_to_bytearray()
#
# loader = AnvilLoader("C:\\Users\\wojci\\AppData\\Roaming\\.minecraft\\saves\\New World (8)\\region\\r.0.0.mca")
# loader.load()
