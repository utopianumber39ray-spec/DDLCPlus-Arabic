"""Apply reviewed Arabic poem line replacements to langar.cy.

The bundle stores RTL multiline strings in reverse line order (ArabicShaper
reverses them at runtime). Patches use 1-based LOGICAL line numbers. Only the
lines listed in the patch JSON are re-encoded; every other segment is kept
byte-identical.

Usage: python3 tools/apply_poem_patches.py <langar.cy> <patches.json>
"""
import json
import sys
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rtl_codec import decode_body, encode_body


def main():
    path = Path(sys.argv[1])
    patches = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    dec = bytes(b ^ 40 for b in path.read_bytes())
    tmp = ROOT / ".work/_apply_patches.cy"
    tmp.write_bytes(dec)
    env = UnityPy.load(str(tmp))
    obj = [o for o in env.objects if o.type.name == "MonoBehaviour"][0]
    tree = obj.read_typetree()
    values = tree["linesdict"][224]["values"]

    grouped = {}
    for patch in patches:
        grouped.setdefault(patch["value"], []).append(patch)

    applied = 0
    for value_index, edits in sorted(grouped.items()):
        raw = values[value_index]
        stored = raw.split("\\n")
        logical = list(reversed(stored))
        for edit in edits:
            line_no = edit["line"]
            if not 1 <= line_no <= len(logical):
                raise ValueError(f"value {value_index}: bad line {line_no}")
            current = decode_body(logical[line_no - 1])
            if current.strip() != edit["old"].strip():
                raise ValueError(
                    f"value {value_index} line {line_no}: expected {edit['old']!r}, got {current!r}"
                )
            logical[line_no - 1] = encode_body(edit["new"])
            applied += 1
        values[value_index] = "\\n".join(reversed(logical))

    obj.save_typetree(tree)
    bundle = env.file.save(packer="original")
    path.write_bytes(bytes(b ^ 40 for b in bundle))
    print(f"applied {applied} line changes across {len(grouped)} values to {path}")


if __name__ == "__main__":
    main()
