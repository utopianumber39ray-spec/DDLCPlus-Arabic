"""Remove pink edges from selected Arabic text in the poem notebook.

Do NOT touch `OutlineColor`: dialogue names intentionally keep their pink
outline. The distortion comes from `Configure(text, false)`, used by
`TryApplyInteractive` on every interactive Arabic TMP (the notebook words),
which applies `OutlineWidth = 0.18`. Setting those width constants to 0
removes the pink halo from selected words while leaving name outlines intact.

Usage: python3 tools/fix_pink_outline.py <ArabicOutlineFix.dll>
"""
import struct
import sys
from pathlib import Path

# IL `ldc.r4 0.18` sites: two in Configure, one field initializer
OFFSETS = (0x6E8, 0x714, 0x17B0)


def main():
    path = Path(sys.argv[1])
    data = bytearray(path.read_bytes())
    # verify the original pink alpha is intact (names must keep their outline)
    alpha = struct.unpack_from("<f", data, 0x817)[0]
    if abs(alpha - 1.0) > 0.01:
        raise ValueError("OutlineColor alpha is not the original 1.0 — restore first")
    for offset in OFFSETS:
        value = struct.unpack_from("<f", data, offset)[0]
        if abs(value - 0.18) > 0.01 and abs(value) > 0.01:
            raise ValueError(f"Unexpected value at 0x{offset:X}: {value}")
        struct.pack_into("<f", data, offset, 0.0)
        print(f"outline width at 0x{offset:X}: {value} -> 0.0")
    path.write_bytes(data)
    print("wrote", path)


if __name__ == "__main__":
    main()
