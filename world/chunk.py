from math import ceil, log2

from nbt.nbt import TAG_Compound, TAG_List, TAG_Long

from util.buf import PacketByteBuf


def encode(heights: list[int], bitsPerEntry: int) -> list[int]:
    a = 64 / bitsPerEntry
    b = (len(heights) + a - 1) / a
    c = a - 1
    d = (1 << bitsPerEntry) - 1
    e: list[int] = []
    f = 0
    for i in range(len(heights)):
        g: int = int(i % a)
        h = heights[i]
        e[g] |= (h & d) << (g * bitsPerEntry)

        if g == c:
            f += 1

    return e


def numberOfLeadingZeros(i: int) -> int:
    if i<=0:return 32 if i==0 else 0
    a = 31
    if i>=1<<16:a-=16;i>>=16
    if i>=1<<8:a-=8;i>>=8
    if i>=1<<4:a-=4;i>>=4
    if i>=1<<2:a-=2;i>>=2
    return a-(i>>1)


def bitsToRepresent(i: int) -> int:
    return 32 - numberOfLeadingZeros(i)


hs: list[int] = []


def encode_1() -> list[int]:
    bitsForHeight = bitsToRepresent(384)
    return encode(hs, bitsForHeight)


def heightmap():
    compound = TAG_Compound()

    e = encode_1()
    print(e)

    motion_blocking = TAG_List(type=TAG_Long, name="MOTION_BLOCKING", value=e)

    compound.tags.append(motion_blocking)

    return compound


class PalettedContainer:
    def __init__(self, bpe: int, palette, *data_array: int):         # vint len + list of i64
        self.buffer = PacketByteBuf(bytearray())
        self.buffer.write_varint(bpe)
        self.buffer.write_bytes(palette)
        self.buffer.write_varint(len(data_array))
        for i in data_array:
            self.buffer.write_long(i)


class ChunkSection:
    def __init__(self, block_count: int, block_states: list[PalettedContainer], biomes: list[PalettedContainer]):
        self.block_count = block_count
        self.block_states = block_states
        self.biomes = biomes

    def write(self) -> bytes:
        buf = PacketByteBuf(bytearray())
        buf.write_short(self.block_count)

        for block_container in self.block_states:
            buf.write_bytes(block_container.buffer.get_data())

        for biome_container in self.biomes:
            buf.write_bytes(biome_container.buffer.get_data())

        return buf.get_data()


print(heightmap())
