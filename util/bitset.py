import math

from util.buf import PacketByteBuf
from util.var import pack_varint


class BitSet:
    def __init__(self, bits_per_entry, entries):
        self.bits_per_entry = bits_per_entry
        self.entries = entries

        # Calculate total bits required to store the entries
        self.total_bits = len(entries) * bits_per_entry

        # Calculate the number of bits needed to be a multiple of 64
        if self.total_bits % 64 != 0:
            self.total_bits_padded = math.ceil(self.total_bits / 64) * 64
        else:
            self.total_bits_padded = self.total_bits

        # Calculate the number of bytes required for the padded bits
        self.total_bytes = self.total_bits_padded // 8

        # Create a bitset with the required padded size
        self.bitset = bytearray(self.total_bytes)

        # Pack the entries into the bitset
        self._pack_entries_into_bitset()

    def _pack_entries_into_bitset(self):
        current_bit = 0  # Track the bit position where we're inserting
        for entry in self.entries:
            # Insert the entry into the bitset, considering the current bit position
            for bit in range(self.bits_per_entry):
                byte_index = (current_bit + bit) // 8
                bit_index = (current_bit + bit) % 8

                # Set the bit in the bitset
                if (entry >> bit) & 1:
                    self.bitset[byte_index] |= (1 << bit_index)
                else:
                    self.bitset[byte_index] &= ~(1 << bit_index)
            current_bit += self.bits_per_entry

    def get(self) -> bytes:
        return pack_varint(self.longs_count()) + self.bitset

    def longs_count(self):
        # A long is 64 bits, so calculate how many longs fit in the bitset
        total_longs = self.total_bits_padded // 64
        return total_longs

    def get_padding(self):
        # Padding is the difference between total padded bits and actual used bits
        padding_bits = self.total_bits_padded - self.total_bits
        return padding_bits

    def display_bitset(self):
        # Display the bitset in binary form
        return ' '.join(f'{byte:08b}' for byte in self.bitset)

# # Example usage:
# bits_per_entry = 5  # Let's say we want 5 bits per entry
# entries = [3, 7, 15, 1]  # These are the entries
#
# bitset = BitSet(bits_per_entry, entries)
# print("Bitset (binary):", bitset.display_bitset())
# print("Number of longs that fit:", bitset.longs_count())
# print("Padding bits:", bitset.get_padding())
