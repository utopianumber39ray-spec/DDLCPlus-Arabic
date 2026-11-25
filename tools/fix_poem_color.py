"""Patch the Renpy poem text styles in sharedassets2.assets to black.

The serialized `level2` TMP colour is not enough: `RenpyPoemUI.OnRefreshStyle`
calls `StyleHelper.ApplyTextStyle`, which resets `Graphic.color` from the
style definition on every poem refresh. The `*_text` styles therefore have
to be black too, otherwise the poem renders white at runtime.

Usage: python3 tools/fix_poem_color.py <path-to-sharedassets2.assets>
"""
import re
import sys
from pathlib import Path

POEM_STYLES = (
    "monika_text", "yuri_text", "yuri_text_2", "yuri_text_3",
    "natsuki_text", "sayori_text",
)


def main():
    path = Path(sys.argv[1])
    data = bytearray(path.read_bytes())
    original = bytes(data)
    for name in POEM_STYLES:
        patched = False
        for match in re.finditer(re.escape(name.encode()), original):
            window = original[match.start():match.start() + 0x100]
            color = re.search(rb"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", window)
            if not color:
                continue
            offset = match.start() + color.start()
            if original[offset:offset + 4] == b"#fff":
                data[offset:offset + 4] = b"#000"
                print(f"{name}: patched #fff -> #000 at 0x{offset:X}")
            elif original[offset:offset + 5] == b"#ffffff":
                data[offset:offset + 4] = b"#000"
                del data[offset + 4:offset + 5]
                print(f"{name}: patched #ffffff -> #000 at 0x{offset:X}")
            patched = True
            break
        if not patched:
            raise ValueError(f"Style colour not found for {name}")
    path.write_bytes(data)
    print("wrote", path)


if __name__ == "__main__":
    main()
