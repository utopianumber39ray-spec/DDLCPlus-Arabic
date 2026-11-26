"""Improve the poem reading layout (spacing and word wrapping).

Two layers must be changed:
  1. `level2` TMP path_id 3220 ("This is a POEM"): reduce font size and add
     line/paragraph spacing.
  2. `sharedassets2.assets` Renpy poem styles: `StyleHelper.ApplyTextStyle`
     re-applies each style's size at runtime, overriding the serialized TMP
     font size. Reduce every poem style size by the same ratio.

Usage: python3 tools/fix_poem_layout.py <level2> <sharedassets2.assets>
"""
import re
import struct
import sys
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import unity_support as support

CHANGES = {
    "m_fontSize": 28.0,
    "m_fontSizeBase": 28.0,
    "m_lineSpacing": 0.85,
    "m_lineSpacingMax": 0.0,
    "m_paragraphSpacing": 0.35,
    "m_wordWrappingRatios": 0.0,
    # Keep each poem line on a single row. Auto-shrinking lets the longest
    # Arabic line fit the page instead of breaking a word in half.
    "m_enableWordWrapping": 0,
    "m_enableAutoSizing": 1,
    "m_fontSizeMin": 12.0,
    "m_fontSizeMax": 28.0,
}
# style name -> original size -> new size (~22% smaller, matching TMP 36 -> 28)
STYLE_SIZES = {
    "monika_text": (54.0, 42.0),
    "yuri_text": (52.0, 40.0),
    "yuri_text_2": (56.0, 44.0),
    "yuri_text_3": (44.0, 34.0),
    "natsuki_text": (52.0, 40.0),
    "sayori_text": (54.0, 42.0),
}


def patch_scene(path):
    support.DATA = ROOT / ".work/game/extracted/Doki Doki Literature Club Plus_Data"
    env = support.configure_environment(UnityPy.load(str(path)))
    obj = [o for o in env.objects if o.path_id == 3220][0]
    tree = obj.read_typetree(nodes=support.mono_node(obj))
    print("before:", {k: tree.get(k) for k in CHANGES})
    for key, value in CHANGES.items():
        if key in tree:
            tree[key] = value
    obj.save_typetree(tree)
    path.write_bytes(env.file.save(packer="original"))
    print("wrote", path)


def patch_styles(path):
    data = bytearray(path.read_bytes())
    for name, (old, new) in STYLE_SIZES.items():
        for match in re.finditer(re.escape(name.encode()), data):
            offset = match.start() + 0x5C
            if offset + 4 > len(data):
                continue
            value = struct.unpack_from("<f", data, offset)[0]
            if abs(value - old) < 0.5:
                struct.pack_into("<f", data, offset, new)
                print(f"{name}: {value} -> {new} at 0x{offset:X}")
                break
            if abs(value - new) < 0.5:
                print(f"{name}: already {new}")
                break
        else:
            raise ValueError(f"Style size not found for {name}")
    path.write_bytes(data)
    print("wrote", path)


def main():
    level2 = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".work/fixes/level2"
    styles = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        ROOT / ".work/game/extracted/Doki Doki Literature Club Plus_Data/sharedassets2.assets"
    )
    patch_scene(level2)
    patch_styles(styles)


if __name__ == "__main__":
    main()
