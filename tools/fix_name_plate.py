"""Fit the Arabic name plate inside its box.

Restore the original vertical offsets in ArabicOutlineFix.dll (+5 generic,
+2 Monika, +3 player) — a larger offset pushed names out of the plate — and
reduce the name TMP font size from 36 to 28 so diacritics stay inside.

Usage: python3 tools/fix_name_plate.py <ArabicOutlineFix.dll> <level2>
"""
import struct
import sys
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import unity_support as support

OFFSETS = ((0x339, 9.0, 5.0), (0x340, 6.0, 2.0), (0x347, 7.0, 3.0))
NAME_TMP = 3347


def main():
    dll = Path(sys.argv[1])
    level2 = Path(sys.argv[2])
    data = bytearray(dll.read_bytes())
    for offset, old, new in OFFSETS:
        value = struct.unpack_from("<f", data, offset)[0]
        if abs(value - old) > 0.01 and abs(value - new) > 0.01:
            raise ValueError(f"Unexpected offset at 0x{offset:X}: {value}")
        struct.pack_into("<f", data, offset, new)
        print(f"name offset 0x{offset:X}: {value} -> {new}")
    dll.write_bytes(data)

    support.DATA = ROOT / ".work/game/extracted/Doki Doki Literature Club Plus_Data"
    env = support.configure_environment(UnityPy.load(str(level2)))
    obj = [o for o in env.objects if o.path_id == NAME_TMP][0]
    tree = obj.read_typetree(nodes=support.mono_node(obj))
    print("name font size before:", tree.get("m_fontSize"))
    tree["m_fontSize"] = 28.0
    tree["m_fontSizeBase"] = 28.0
    obj.save_typetree(tree)
    level2.write_bytes(env.file.save(packer="original"))
    print("wrote", level2)


if __name__ == "__main__":
    main()
