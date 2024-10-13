from util import var


class Number:
    def __init__(self, min_value: int, max_value: int, value: int):
        if (value > max_value) or (value < min_value):
            raise ValueError(f"Value {value} out of bounds for {min_value} - {max_value}")
        else:
            self.value = value


class U8(Number):
    MIN_VALUE = 0x00
    MAX_VALUE = 0xff

    def __init__(self, value: int):
        super().__init__(U8.MIN_VALUE, U8.MAX_VALUE, value)


class I16(Number):
    MIN_VALUE = -0x8000
    MAX_VALUE = 0x7fff

    def __init__(self, value: int):
        super().__init__(I16.MIN_VALUE, I16.MAX_VALUE, value)


class I64(Number):
    MIN_VALUE = -0x8000000000000000
    MAX_VALUE = 0x7fffffffffffffff

    def __init__(self, value: int):
        super().__init__(I64.MIN_VALUE, I64.MAX_VALUE, value)


class Vint(Number):
    MIN_VALUE = 0x00
    MAX_VALUE = 0xffffffffff

    def __init__(self, value: int):
        super().__init__(Vint.MIN_VALUE, Vint.MAX_VALUE, value)

        self.bytes = var.pack_varint(value)
