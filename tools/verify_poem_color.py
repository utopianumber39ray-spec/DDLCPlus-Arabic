"""Verify the poem reading text colour in level2 (black = fixed)."""
import sys
from pathlib import Path
import UnityPy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import unity_support as support

def main():
    data = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".work/extracted/Doki Doki Literature Club Plus_Data"
    support.DATA = data
    env = support.configure_environment(UnityPy.load(str(data / "level2"), str(data / "globalgamemanagers.assets")))
    entries = {(o.assets_file.name, o.path_id): o for o in env.objects}
    obj = entries[("level2", 3220)]
    tree = obj.read_typetree(nodes=support.mono_node(obj))
    color = tree["m_fontColor"]
    rgba = tree["m_fontColor32"]["rgba"]
    ok = all(color[k] == 0.0 for k in ("r", "g", "b")) and rgba == 0xFF000000
    print("POEM_COLOR", "BLACK" if ok else f"NOT_BLACK {color} {hex(rgba)}")
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
