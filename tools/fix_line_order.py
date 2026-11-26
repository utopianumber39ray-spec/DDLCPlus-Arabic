"""Store RTL multiline strings in display order.

`DDLCArabic.TextFlow.RewrapCore()` in ArabicShaper.dll reverses the lines of
every RTL multiline string at runtime. To display in the logical order, the
stored segments must therefore be the reverse of the logical/English order.

This tool reverses the literal `\n`-delimited segments of the affected
group-224 values in langar.cy, leaving non-display data (302) and the block
art (508) untouched. See .work/line_order_report.md for the evidence.
"""
import sys
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]

INDICES = {
    25, 27, 31, 37, 39, 47, 84, 99, 101, 103,
    151, 153, 155, 157, 159, 161, 164, 165, 167, 169, 171, 173, 174, 175,
    177, 179, 181, 183, 191, 193, 195, 197,
    206, 207, 208, 209, 210, 211,
    272, 273, 274, 275, 286, 288, 290, 292, 294, 296, 298, 300, 301, 303,
    304, 305,
    343,
    502, 505, 510, 513, 514, 515, 516, 517, 521, 522, 523,
    582, 583,
    662, 664, 666, 667, 668, 669, 670, 671, 672, 673,
}


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".work/fixes/langar.cy"
    dec = bytes(b ^ 40 for b in path.read_bytes())
    tmp = ROOT / ".work/_lineorder.cy"
    tmp.write_bytes(dec)
    env = UnityPy.load(str(tmp))
    obj = [o for o in env.objects if o.type.name == "MonoBehaviour"][0]
    tree = obj.read_typetree()
    values = tree["linesdict"][224]["values"]
    changed = 0
    for index in sorted(INDICES):
        raw = values[index]
        if "\\n" not in raw:
            raise ValueError(f"value {index} has no literal newline")
        values[index] = "\\n".join(reversed(raw.split("\\n")))
        changed += 1
    obj.save_typetree(tree)
    bundle = env.file.save(packer="original")
    path.write_bytes(bytes(b ^ 40 for b in bundle))
    print(f"reversed {changed} values in {path}")


if __name__ == "__main__":
    main()
