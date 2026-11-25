"""Verify Monika's 'Hole in the Wall' poem line order in langar.cy."""
import sys
from pathlib import Path
import UnityPy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rtl_codec import decode_raw

def main():
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".work/fixes/langar.cy"
    dec = bytes(b ^ 40 for b in p.read_bytes())
    tmp = ROOT / ".work/fixes/_lang_check.cy"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(dec)
    env = UnityPy.load(str(tmp))
    obj = [o for o in env.objects if o.type.name == "MonoBehaviour"][0]
    s = decode_raw(obj.read_typetree()["linesdict"][224]["values"][174]).replace("\\n", "\n")
    lines = [x for x in s.split("\n") if x.strip()]
    first_ok = "It couldn't have been me" in lines[0] or " concede" in lines[0] or "can't be" in lines[0] or "لا يمكن" in lines[0] or "منّي" in lines[0]
    last_ok = "was looking in" in lines[-1] or "ينظر" in lines[-1] and "الداخل" in lines[-1]
    print("POEM_ORDER", "OK" if (first_ok and last_ok) else f"CHECK first={lines[0][:60]!r} last={lines[-1][:60]!r}")

if __name__ == "__main__":
    main()
