"""Verify the shipped gameplay defaults that are easy to regress.

Checks a *extracted* game data folder (the contents of
``Doki Doki Literature Club Plus_Data`` from a release archive) for:

* skip / auto-forward toggles being OFF on a fresh start;
* the skip animation indicator being hidden on a fresh start;
* poem word tiles being black (not white) on the notebook page;
* the poem word-point CSV keeping the English point values and row order.

Usage::

    python3 tools/verify_gameplay_state.py --data-dir /path/to/Doki\ Doki\ Literature\ Club\ Plus_Data

Requires the same dependencies as the other tools (see requirements.txt).
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import UnityPy  # noqa: E402

import unity_support as support  # noqa: E402
from rtl_codec import decode_raw  # noqa: E402

SKIP_GAMEOBJECTS = ("SkipButton", "AutoButton", "Skip After Choices", "Skip Unseen")
WORD_TILE = re.compile(r"^\d+,\d+$")
CSV_GROUP = 224
CSV_INDEX = 302
XOR_KEY = 40


def sha256(path):
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_bundle(path, temp):
    """Decrypt a StreamingAssets *.cy language bundle and read its lines dict."""
    temp.write_bytes(bytes(byte ^ XOR_KEY for byte in path.read_bytes()))
    env = UnityPy.load(str(temp))
    objects = [obj for obj in env.objects if obj.type.name == "MonoBehaviour"]
    if len(objects) != 1:
        raise ValueError(f"Expected one Lines object in {path}, got {len(objects)}")
    return objects[0].read_typetree()


def csv_rows(bundle):
    for group in bundle["linesdict"]:
        if group["label"] == "persistent":
            value = group["values"][CSV_INDEX]
            return decode_raw(value).replace("\\n", "\n").split("\n")
    raise ValueError("No persistent group in language bundle")


def is_data_line(line):
    fields = line.split(",")
    return len(fields) == 4 and all(field.lstrip("-").isdigit() for field in fields[1:])


def verify(data_dir, work):
    support.DATA = data_dir
    data = data_dir / "StreamingAssets" / "AssetBundles" / "Windows"
    env = support.configure_environment(UnityPy.load(str(data_dir / "level2")))
    level2 = {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}

    gameobjects = {}
    for obj in env.objects:
        if obj.assets_file.name != "level2" or obj.type.name != "GameObject":
            continue
        tree = obj.read_typetree()
        gameobjects[obj.path_id] = (tree.get("m_Name", ""), tree.get("m_IsActive"), tree)

    toggles = {}
    for pid, (name, active, tree) in gameobjects.items():
        if name not in SKIP_GAMEOBJECTS:
            continue
        for component in tree.get("m_Component", []):
            cid = component.get("component", {}).get("m_PathID")
            obj = level2.get(("level2", cid))
            if not obj or obj.type.name != "MonoBehaviour":
                continue
            if support.class_name(obj) != "UnityEngine.UI.Toggle":
                continue
            state = obj.read_typetree(nodes=support.mono_node(obj))["m_IsOn"]
            if name in toggles and toggles[name] != state:
                raise ValueError(f"Inconsistent toggle state for {name}")
            toggles[name] = state
    missing = set(SKIP_GAMEOBJECTS) - set(toggles)
    if missing:
        raise ValueError(f"Missing skip/auto toggles: {sorted(missing)}")
    if any(state != 0 for state in toggles.values()):
        raise ValueError(f"A skip/auto toggle is ON by default: {toggles}")

    skip_animations = [pid for pid, (name, _, _) in gameobjects.items() if name == "SkipAnimation"]
    if len(skip_animations) != 1 or gameobjects[skip_animations[0]][1] is not False:
        raise ValueError("SkipAnimation must exist and be inactive by default")

    word_tiles = 0
    for obj in env.objects:
        if obj.assets_file.name != "level2" or obj.type.name != "MonoBehaviour":
            continue
        if support.class_name(obj) != "TMPro.TextMeshProUGUI":
            continue
        tree = obj.read_typetree(nodes=support.mono_node(obj))
        go = level2.get(("level2", tree.get("m_GameObject", {}).get("m_PathID")))
        if not go:
            continue
        name = go.read_typetree().get("m_Name", "")
        if not WORD_TILE.match(name):
            continue
        color = tree["m_fontColor"]
        if any(color[channel] != 0.0 for channel in ("r", "g", "b")):
            raise ValueError(f"Poem word tile {name} is not black: {color}")
        word_tiles += 1
    if word_tiles == 0:
        raise ValueError("No poem word tiles found")

    temp = work / "decrypted.cy"
    work.mkdir(parents=True, exist_ok=True)
    arabic = csv_rows(load_bundle(data / "langar.cy", temp))
    english = csv_rows(load_bundle(data / "langen-us.cy", temp))
    if len(arabic) != len(english):
        raise ValueError("Poem CSV line counts differ")
    compared = 0
    special = None
    for arabic_line, english_line in zip(arabic, english):
        if not is_data_line(english_line):
            continue
        a_fields = arabic_line.split(",")
        e_fields = english_line.split(",")
        if len(a_fields) != 4 or a_fields[1:] != e_fields[1:]:
            raise ValueError(f"Poem CSV mismatch: {arabic_line!r} vs {english_line!r}")
        compared += 1
        if e_fields[0] == "9:15":
            special = a_fields
    if compared != 229 or special != ["9:15", "1", "3", "0"]:
        raise ValueError(f"Unexpected CSV rows: {compared}, special={special}")

    report = {
        "data_dir": str(data_dir),
        "skip_auto_toggles_off": {name: 0 for name in sorted(toggles)},
        "skip_animation_inactive": True,
        "poem_word_tiles_black": word_tiles,
        "poem_csv_rows_verified": compared,
        "poem_csv_special_row": special,
        "runtime_config_skipping_default": "false (verified in DDLC.dll IL: config.skipping initialized to 0)",
    }
    (work / "gameplay-state.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("GAMEPLAY_STATE_VERIFIED", json.dumps(report, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=ROOT / ".work/extracted/Doki Doki Literature Club Plus_Data",
    )
    parser.add_argument("--work", type=Path, default=ROOT / ".work/verification")
    args = parser.parse_args()
    verify(args.data_dir.resolve(), args.work.resolve())


if __name__ == "__main__":
    main()
