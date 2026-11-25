"""Verify Monika's 'Hole in the Wall' poem line order in langar.cy.

The poem is stored as 14 presentation-form lines joined by literal ``\\n``.
It must be in the same order as the English original: the first line is
"It couldn't have been me" and the last is "...was looking in".
"""
import sys
from pathlib import Path
import UnityPy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rtl_codec import decode_body

FIRST = ("لا يمكن", "منّي", "It couldn't have been me", "can't be")
LAST = ("ينظر", "look")


def main():
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".work/fixes/langar.cy"
    dec = bytes(b ^ 40 for b in p.read_bytes())
    tmp = ROOT / ".work/fixes/_lang_check.cy"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(dec)
    env = UnityPy.load(str(tmp))
    obj = [o for o in env.objects if o.type.name == "MonoBehaviour"][0]
    raw = obj.read_typetree()["linesdict"][224]["values"][174]
    lines = [decode_body(x).strip() for x in raw.split("\\n") if x.strip()]
    first_ok = any(x in lines[0] for x in FIRST)
    last_ok = any(x in lines[-1] for x in LAST)
    ok = len(lines) == 14 and first_ok and last_ok
    print("POEM_ORDER", "OK" if ok else
          f"CHECK lines={len(lines)} first={lines[0][:60]!r} last={lines[-1][:60]!r}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
