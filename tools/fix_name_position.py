"""Raise the Arabic dialogue name plate so diacritics stay inside the box.

`ArabicOutlineFix.ApplyDialogueName` offsets the name TMP vertically by
+5 (generic), +3 (player) or +2 (Monika). With the Arabic font the dots of
letters like ي fall below the plate. Raise all three by 4 units.

Usage: python3 tools/fix_name_position.py <ArabicOutlineFix.dll>
"""
import struct
import sys
from pathlib import Path

# float offsets in ApplyDialogueName: generic, Monika, player
OFFSETS = ((0x339, 5.0, 9.0), (0x340, 2.0, 6.0), (0x347, 3.0, 7.0))


def main():
    path = Path(sys.argv[1])
    data = bytearray(path.read_bytes())
    for offset, old, new in OFFSETS:
        value = struct.unpack_from("<f", data, offset)[0]
        if abs(value - old) > 0.01 and abs(value - new) > 0.01:
            raise ValueError(f"Unexpected value at 0x{offset:X}: {value}")
        struct.pack_into("<f", data, offset, new)
        print(f"name offset at 0x{offset:X}: {value} -> {new}")
    path.write_bytes(data)
    print("wrote", path)


if __name__ == "__main__":
    main()
