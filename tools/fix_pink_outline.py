"""Remove distorted pink edges from selected Arabic words in the poem notebook.

Two changes in ArabicOutlineFix.dll:
  1. Interactive outline width constants (0.18) -> 0.
  2. `Configure()` uses `HistoryColor` (dark maroon) instead of the pink
     `OutlineColor` for interactive TMPs. `ApplyDialogueName()` keeps using
     `OutlineColor`, so character name plates retain their pink outline.

Usage: python3 tools/fix_pink_outline.py <ArabicOutlineFix.dll>
"""
import dnfile
import struct
import sys
from pathlib import Path

WIDTH_OFFSETS = (0x6E8, 0x714, 0x17B0)
OLD_FIELD = bytes.fromhex("7e01000004")   # ldsfld OutlineColor (field 0x04000001)
NEW_FIELD = bytes.fromhex("7e02000004")   # ldsfld HistoryColor (field 0x04000002)


def rva_to_offset(pe, rva):
    for section in pe.sections:
        base = section.VirtualAddress
        if base <= rva < base + max(section.Misc_VirtualSize, section.SizeOfRawData):
            return section.PointerToRawData + (rva - base)
    raise ValueError(f"RVA {rva} outside sections")


def main():
    path = Path(sys.argv[1])
    pe = dnfile.dnPE(str(path))
    data = bytearray(path.read_bytes())
    alpha = struct.unpack_from("<f", data, 0x817)[0]
    if abs(alpha - 1.0) > 0.01:
        raise ValueError("OutlineColor alpha must be the original 1.0")
    for offset in WIDTH_OFFSETS:
        value = struct.unpack_from("<f", data, offset)[0]
        if abs(value - 0.18) > 0.01 and abs(value) > 0.01:
            raise ValueError(f"Unexpected outline width at 0x{offset:X}: {value}")
        struct.pack_into("<f", data, offset, 0.0)

    rva = [m.struct.Rva for m in pe.net.mdtables.MethodDef if str(m.Name) == "Configure"][0]
    offset = rva_to_offset(pe, rva)
    first = data[offset]
    il = offset + 1 if (first & 3) == 2 else offset + ((struct.unpack_from("<H", data, offset)[0] >> 12) * 4)
    size = (first >> 2) if (first & 3) == 2 else struct.unpack_from("<I", data, offset + 4)[0]
    body = data[il:il + size]
    count = body.count(OLD_FIELD)
    if count not in (0, 2):
        raise ValueError(f"Expected 0 or 2 OutlineColor loads in Configure, got {count}")
    body = body.replace(OLD_FIELD, NEW_FIELD)
    data[il:il + size] = body
    path.write_bytes(data)
    print(f"patched {count} Configure outline colours and {len(WIDTH_OFFSETS)} width constants")


if __name__ == "__main__":
    main()
