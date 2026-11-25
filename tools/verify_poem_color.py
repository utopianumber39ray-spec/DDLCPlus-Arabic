"""Verify the poem reading text colour (black = fixed).

Two independent checks are required:
  1. `level2` TMP path_id 3220 ("This is a POEM") serialized font colour.
  2. `sharedassets2.assets` Renpy style definitions: the poem-specific
     `*_text` styles are applied at runtime by `StyleHelper.ApplyTextStyle`
     on every poem refresh, overwriting the serialized colour. They must
     also be black, otherwise the poem renders white in game.
"""
import re
import sys
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import unity_support as support

POEM_STYLES = (
    "monika_text", "yuri_text", "yuri_text_2", "yuri_text_3",
    "natsuki_text", "sayori_text",
)


def verify_scene(data):
    support.DATA = data
    env = support.configure_environment(UnityPy.load(str(data / "level2")))
    entries = {(o.assets_file.name, o.path_id): o for o in env.objects}
    obj = entries[("level2", 3220)]
    tree = obj.read_typetree(nodes=support.mono_node(obj))
    color = tree["m_fontColor"]
    rgba = tree["m_fontColor32"]["rgba"]
    return all(color[k] == 0.0 for k in ("r", "g", "b")) and rgba == 0xFF000000, color, rgba


def verify_styles(data):
    raw = (data / "sharedassets2.assets").read_bytes()
    results = {}
    for name in POEM_STYLES:
        results[name] = "MISSING"
        for match in re.finditer(re.escape(name.encode()), raw):
            window = raw[match.start():match.start() + 0x100]
            color = re.search(rb"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", window)
            if color:
                results[name] = color.group().decode()
                break
    return results


def main():
    data = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".work/extracted/Doki Doki Literature Club Plus_Data"
    scene_ok, color, rgba = verify_scene(data)
    styles = verify_styles(data)
    styles_ok = all(value == "#000" for value in styles.values())
    ok = scene_ok and styles_ok
    print("POEM_COLOR_SCENE", "BLACK" if scene_ok else f"NOT_BLACK {color} {hex(rgba)}")
    print("POEM_COLOR_STYLES", styles, "OK" if styles_ok else "NOT_BLACK")
    print("POEM_COLOR", "BLACK" if ok else "NOT_BLACK")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
