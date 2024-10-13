import struct
from abc import abstractmethod
from io import BytesIO

import nbtlib

from anvil.anvilconv import blocks_dict
from anvil.chunk_io import MCAIO, ChunkIO, Util
from anvil.jtypes import U8, Vint, I64, I16
from util.buf import PacketByteBuf


class Palette:
    @abstractmethod
    def to_bytes(self) -> bytes: ...


class SingleValuedPalette(Palette):
    def __init__(self, value: Vint):
        self.value = value.bytes

    def to_bytes(self) -> bytes:
        return self.value


class IndirectPalette(Palette):
    def __init__(self, array_length: Vint, palette: list[Vint]):
        self.array_length = array_length.bytes
        self.palette: list[bytes] = []

        for e in palette:
            self.palette.append(e.bytes)

    def to_bytes(self) -> bytes:
        arr = bytearray()
        arr.extend(self.array_length)

        for item in self.palette:
            arr.extend(item)

        return arr


class PalettedContainer:
    def __init__(self, bits_per_entry: U8, palette: Palette, data_array_length: Vint,
                 data_array: list[I64]):

        self.bits_per_entry = bits_per_entry.value
        self.palette = palette
        self.data_array_length = data_array_length.bytes
        self.data_array: list[bytes] = []

        for i64 in data_array:
            self.data_array.append(i64.value.to_bytes(8, signed=True))

    def to_bytes(self) -> bytes:
        arr = bytearray()
        arr.extend(self.bits_per_entry.to_bytes(1))
        arr.extend(self.palette.to_bytes())
        arr.extend(self.data_array_length)

        for item in self.data_array:
            arr.extend(item)

        return arr


class ChunkSection:
    def __init__(self, block_count: I16, block_states: PalettedContainer, biomes: PalettedContainer):
        self.block_count = block_count.value
        self.block_states = block_states.to_bytes()
        self.biomes = biomes.to_bytes()

    def to_bytes(self) -> bytes:
        arr = bytearray()
        arr.extend(self.block_count.to_bytes(2))
        arr.extend(self.block_states)
        arr.extend(self.biomes)

        return arr


async def extract_chunk_data(root: str, x: int, z: int) -> ChunkIO:
    which_mca: tuple[int, int] = MCAIO.get_mca(x, z)
    whole_file_buf: PacketByteBuf = PacketByteBuf.of_file(f"{root}/r.{which_mca[0]}.{which_mca[1]}.mca")

    locations_table = whole_file_buf.read_bytes(4096)
    whole_file_buf.read_bytes(4096)

    location_entry_offset = MCAIO.get_location_entry_offset(x, z)

    location_entry = struct.unpack(">I", locations_table[location_entry_offset: location_entry_offset + 4])[0]

    entry_offset_and_size = MCAIO.chunk_location(location_entry)

    chunk_data = whole_file_buf.get_data()[
                 entry_offset_and_size[0]: entry_offset_and_size[0] + entry_offset_and_size[1]]

    return ChunkIO(chunk_data)


async def get_chunk_sections(data: ChunkIO) -> list[ChunkSection]:
    li: list[ChunkSection] = []

    nbt: nbtlib.Compound = data.get_decompressed_nbt()
    nbt_sections = nbt["sections"]

    for nbt_section in nbt_sections:
        nbt_block_states: nbtlib.Compound = nbt_section["block_states"]
        nbt_palette: nbtlib.List[nbtlib.Compound] = nbt_block_states["palette"]
        air_palette: int = Util.get_palette_id(nbt_palette, "minecraft:air")

        try:
            nbt_data_array: nbtlib.List[nbtlib.Long] = nbt_block_states["data"]
        except KeyError:
            if nbt_palette[0]["Name"] == "minecraft:air":
                block_count = 0
            else:
                block_count = 4096

            section = ChunkSection(I16(block_count),
                                   PalettedContainer(
                U8(0), SingleValuedPalette(Vint(1)), Vint(0), []),
                                   PalettedContainer(
                U8(0), SingleValuedPalette(Vint(10)), Vint(0), []))

            li.append(section)

            continue

        longs: int = len(nbt_data_array)
        bits_per_entry: int = Util.get_bpe(longs)

        block_count = Util.get_block_count(air_palette, bits_per_entry, nbt_data_array)

        if bits_per_entry == 0:
            block = nbt_palette[0]["Name"]

            states = blocks_dict[block]["states"]

            palette: SingleValuedPalette = SingleValuedPalette(Vint(states[0]["id"]))
        elif bits_per_entry <= 8:
            array: list[Vint] = []

            for nbt_palette_entry in nbt_palette:
                temp = blocks_dict[nbt_palette_entry["Name"]]["states"][0]["id"]
                array.append(Vint(temp))

            palette: IndirectPalette = IndirectPalette(Vint(len(array)), array)
        else:
            palette: Palette = Palette()

        arr: list[I64] = []

        for entry in nbt_data_array:
            arr.append(I64(entry))

        block_states = PalettedContainer(U8(bits_per_entry), palette, Vint(len(nbt_data_array)), arr)

        biomes = PalettedContainer(U8(0), SingleValuedPalette(Vint(10)), Vint(26),
                                   [I64(I64.MAX_VALUE) for i in range(26)])

        section = ChunkSection(I16(block_count), block_states, biomes)

        li.append(section)

    return li


async def chunk_sections_to_bytes(*sections: ChunkSection) -> bytes:
    bytez: bytearray = bytearray()

    for section in sections:
        bytez.extend(section.to_bytes())

    return bytez


async def make_packet(x: int, z: int, heightmaps: nbtlib.Compound, sections: bytes) -> PacketByteBuf:
    buf: PacketByteBuf = PacketByteBuf.empty()
    packet_buf: PacketByteBuf = PacketByteBuf.empty()

    # packet id
    buf.write_varint(0x25)

    # chunk x
    buf.write_int(x)
    # chunk z
    buf.write_int(z)

    # heightmaps
    bytes_io = BytesIO()
    heightmaps.write(bytes_io)

    buf.write_bytes(bytearray([0x0A]) + bytes_io.getvalue() + bytearray([0x00]))

    # size of data array in bytes
    buf.write_varint(len(sections))

    # DEBUG
    print("Length of sections:", len(sections))

    # data byte array (chunk sections array)
    buf.write_bytes(sections)

    # number of block entities
    buf.write_byte(0)

    # skip any block entities

    # skylight mask
    buf.write_bytes(0b11111111_11111111_11111111_11.to_bytes(4))

    # block light mask
    buf.write_bytes(0b11111111_11111111_11111111_11.to_bytes(4))

    # empty skylight mask
    buf.write_bytes(0b00000000_00000000_00000000_00.to_bytes(4))

    # empty block light mask
    buf.write_bytes(0b00000000_00000000_00000000_00.to_bytes(4))

    # skylight array count
    buf.write_byte(26)

    # length of the following array in bytes (always 2048)
    buf.write_varint(2048)

    # skylight array
    buf.write_bytes(bytearray([0xff for i in range(2048)]))

    # block light array count
    buf.write_byte(26)

    # length of the following array in bytes (always 2048)
    buf.write_varint(2048)

    # block light array
    buf.write_bytes(bytearray([0xff for i in range(2048)]))

    # packet length prefix
    packet_buf.write_varint(len(buf.get_data()))

    # DEBUG
    print("whole data length:", len(buf.get_data()))

    # rest of the data
    packet_buf.write_bytes(buf.get_data())

    return packet_buf
