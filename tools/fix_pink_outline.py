"""Remove the hard-coded pink outline from ArabicOutlineFix.dll.

`ArabicOutlineFix.OutlineColor` is (1.0, 0.55, 0.72, 1.0) — a pink outline
applied to every interactive Arabic TextMeshProUGUI. On the poem word notebook
this shows as pink/distorted edges around the words. Setting the alpha to 0
keeps every other behaviour unchanged while making the outline invisible.

Usage: python3 tools/fix_pink_outline.py <ArabicOutlineFix.dll>
"""
import struct
import sys
from pathlib import Path

# file offsets of the four floats of OutlineColor in the released DLL
OFFSETS = (0x808, 0x80D, 0x812, 0x817)


def main():
    path = Path(sys.argv[1])
    data = bytearray(path.read_bytes())
    expected = (1.0, 0.55, 0.72, 1.0)
    for offset, value in zip(OFFSETS, expected):
        actual = struct.unpack_from("<f", data, offset)[0]
        if abs(actual - value) > 0.01:
            raise ValueError(f"Unexpected value at 0x{offset:X}: {actual}")
    struct.pack_into("<f", data, OFFSETS[-1], 0.0)
    path.write_bytes(data)
    print(f"patched OutlineColor alpha to 0 at 0x{OFFSETS[-1]:X}: {path}")


if __name__ == "__main__":
    main()
