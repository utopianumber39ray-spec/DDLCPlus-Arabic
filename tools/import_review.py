import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".work"
sys.path.insert(0, str(ROOT / "tools"))
from poem_csv import reordered_csv
from rtl_codec import TOKEN_RE, decode_body, decode_raw, encode_body

SOURCE = WORK / "decrypted/langar.cy.bundle"
ENGLISH = WORK / "decrypted/langen-us.cy.bundle"
RUNTIME = WORK / "original/langar.cy"
OUTPUT = WORK / "final"
IDENTITY = ("id", "label", "key", "index", "en")
CSV_GROUP = 224
CSV_INDEX = 302


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def language_data(path):
    env = UnityPy.load(str(path))
    objects = [obj for obj in env.objects if obj.type.name == "MonoBehaviour"]
    if len(objects) != 1:
        raise ValueError(f"Expected one Lines object in {path}, got {len(objects)}")
    return env, objects[0], objects[0].read_typetree()


def load_records():
    paths = sorted((ROOT / "localization/revised").glob("part_*.jsonl"))
    records = [json.loads(line) for path in paths for line in path.read_text(encoding="utf-8").splitlines()]
    original = [json.loads(line) for line in (ROOT / "localization/original.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(paths) != 21 or len(records) != 16174 or len(original) != 16174:
        raise ValueError("Review part or record count differs")
    if [row["id"] for row in records] != list(range(16174)):
        raise ValueError("Review record sequence differs")
    for row, source in zip(records, original):
        if any(row[key] != source[key] for key in IDENTITY):
            raise ValueError(f"Review identity differs at {row['id']}")
        if row["reviewed"] is not True or not isinstance(row["ar"], str):
            raise ValueError(f"Unreviewed or invalid record {row['id']}")
        if not row["ar"] and source["en"]:
            raise ValueError(f"Unexpected blank translation {row['id']}")
    return records, original


def canonical(text):
    reordered = "".join(sorted(unicodedata.normalize("NFD", text), key=unicodedata.combining))
    normalized = unicodedata.normalize("NFKC", reordered)
    closing = normalized.find("</i>")
    opening = normalized.find("<i>")
    if closing >= 0 and (opening < 0 or closing < opening):
        normalized = normalized.replace("</i>", "\0").replace("<i>", "</i>").replace("\0", "<i>")
    return normalized


def encode_display_text(text):
    lines = []
    for line in text.split("\\n"):
        if any("\ufb50" <= char <= "\ufeff" for char in line):
            lines.append(line)
        elif any("\u0600" <= char <= "\u06ff" for char in line):
            lines.append(encode_body(line))
        else:
            lines.append(line)
    return "\\n".join(lines)


def encode_translation(original, logical, record_id):
    if "<align=right>" not in original:
        return encode_display_text(logical)
    original_lines = original.split("\n")
    logical_lines = logical.split("\n")
    if len(original_lines) != len(logical_lines):
        raise ValueError(f"Hard line break count differs at {record_id}")
    output = []
    for old, new in zip(original_lines, logical_lines):
        prefix = "<align=right>" if old.startswith("<align=right>") else ""
        suffix = "</align>" if old.endswith("</align>") else ""
        if not prefix or not suffix:
            raise ValueError(f"Alignment style differs at {record_id}")
        body = encode_body(new)
        encoded = prefix + body + suffix
        if Counter(TOKEN_RE.findall(body)) != Counter(TOKEN_RE.findall(new)):
            raise ValueError(f"Protected tokens differ at {record_id}")
        if not re.search(r"[A-Za-z]", new) and canonical(decode_raw(encoded)) != canonical(new):
            raise ValueError(f"Arabic encoding differs at {record_id}")
        output.append(encoded)
    return "\n".join(output)


def main():
    records, original = load_records()
    env, obj, arabic = language_data(SOURCE)
    _, _, english = language_data(ENGLISH)
    if len(arabic["linesdict"]) != 226 or len(english["linesdict"]) != 226:
        raise ValueError("Scene count differs")
    changed = 0
    index = 0
    expected_values = []
    for group_index, (group, english_group) in enumerate(zip(arabic["linesdict"], english["linesdict"])):
        if group["label"] != english_group["label"] or group["keys"] != english_group["keys"]:
            raise ValueError(f"Scene identity differs at {group_index}")
        if not len(group["keys"]) == len(group["values"]) == len(english_group["values"]):
            raise ValueError(f"Scene value count differs at {group_index}")
        for value_index in range(len(group["values"])):
            row, source = records[index], original[index]
            if (row["label"], row["key"], row["index"]) != (group["label"], group["keys"][value_index], value_index):
                raise ValueError(f"Bundle identity differs at {index}")
            original_raw = group["values"][value_index]
            if decode_raw(original_raw) != source["ar"]:
                raise ValueError(f"Source bundle differs at {index}")
            if row["ar"] != source["ar"] and not (group_index == CSV_GROUP and value_index == CSV_INDEX):
                original_raw = encode_translation(original_raw, row["ar"], index)
                group["values"][value_index] = original_raw
                changed += 1
            expected_values.append(original_raw)
            index += 1
    if index != 16174:
        raise ValueError("Not all reviewed translations were applied")
    group = arabic["linesdict"][CSV_GROUP]
    expected_csv = reordered_csv(group["values"][CSV_INDEX], english["linesdict"][CSV_GROUP]["values"][CSV_INDEX])
    group["values"][CSV_INDEX] = expected_csv
    csv_id = next(i for i, row in enumerate(records) if row["label"] == "persistent" and row["index"] == CSV_INDEX)
    expected_values[csv_id] = expected_csv
    obj.save_typetree(arabic)
    OUTPUT.mkdir(exist_ok=True)
    bundle_path = OUTPUT / "langar.cy.bundle"
    bundle_path.write_bytes(env.file.save(packer="original"))
    _, _, reloaded = language_data(bundle_path)
    actual_values = [value for group in reloaded["linesdict"] for value in group["values"]]
    if len(actual_values) != len(expected_values):
        raise ValueError("Reloaded value count differs")
    for index, (actual, expected) in enumerate(zip(actual_values, expected_values)):
        if actual != expected:
            raise ValueError(f"Reloaded translation differs at {index}")
    if bytes(byte ^ 40 for byte in RUNTIME.read_bytes()) != SOURCE.read_bytes():
        raise ValueError("Original XOR bundle does not match decrypted source")
    runtime_path = OUTPUT / "langar.cy"
    runtime_path.write_bytes(bytes(byte ^ 40 for byte in bundle_path.read_bytes()))
    if bytes(byte ^ 40 for byte in runtime_path.read_bytes()) != bundle_path.read_bytes():
        raise ValueError("Runtime XOR roundtrip differs")
    report = {
        "records": len(records),
        "reviewed": sum(row["reviewed"] for row in records),
        "changed_translations": changed,
        "poetry_csv_reordered_rows": 228,
        "poetry_csv_special_row_preserved": "9:15,1,3,0",
        "source_sha256": sha256(SOURCE),
        "bundle_sha256": sha256(bundle_path),
        "runtime_sha256": sha256(runtime_path),
        "xor_key": 40,
        "logical_reload_verified": True,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FINAL_LANGUAGE_BUNDLE_VERIFIED", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
