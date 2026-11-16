import argparse
import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
MANAGED_REPORT = json.loads(
    (ROOT / ".work/technical/candidate_managed/managed_candidate.json").read_text(encoding="utf-8")
)
REPLACEMENTS = {
    "Doki Doki Literature Club Plus_Data/resources.assets": (
        ".work/technical/candidate/resources.assets",
        "4180a4c380e26274592d5a1197bf96e6445f077a734ff1a2b56399221413d499",
    ),
    "Doki Doki Literature Club Plus_Data/sharedassets1.assets": (
        ".work/technical/candidate/sharedassets1.assets",
        "f6145e7dc7b6c436a19645bfc59b232a752343afa6e4d089cef73abda401dbb7",
    ),
    "Doki Doki Literature Club Plus_Data/Managed/DDLC.dll": (
        ".work/technical/candidate_managed/DDLC.dll",
        "c10499e0bba181a27cf95de0ecfc38b5d59ef9b0f7710795cdb9cca9695da8d5",
    ),
    "Doki Doki Literature Club Plus_Data/Managed/TextTypewriterEffect.dll": (
        ".work/technical/candidate_managed/TextTypewriterEffect.dll",
        MANAGED_REPORT["typewriter_sha256"],
    ),
    "Doki Doki Literature Club Plus_Data/StreamingAssets/AssetBundles/Windows/langar.cy": (
        ".work/final/langar.cy",
        "3d6aab4307671db80d8fee45bf2cc4e0cf6862a3e573f74877ce3be424c1c7ca",
    ),
}
HELPER_NAME = "Doki Doki Literature Club Plus_Data/Managed/ArabicOutlineFix.dll"
HELPER_PATH = ".work/technical/candidate_managed/ArabicOutlineFix.dll"
HELPER_SHA256 = MANAGED_REPORT["helper_sha256"]


def sha256_stream(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def sha256_path(path):
    with path.open("rb") as stream:
        return sha256_stream(stream)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=ROOT / ".work/DDLCPlus-Arabic-Full-v1.2.2.zip")
    parser.add_argument("--output", type=Path, default=ROOT / ".work/DDLCPlus-Arabic-Full-v1.3.3.zip")
    args = parser.parse_args()
    baseline = args.baseline.resolve()
    output = args.output.resolve()
    partial = output.with_suffix(output.suffix + ".partial")
    if output.exists() or partial.exists():
        raise FileExistsError(f"Refusing to overwrite {output} or {partial}")
    sources = {name: ROOT / relative for name, (relative, _) in REPLACEMENTS.items()}
    for name, (relative, expected) in REPLACEMENTS.items():
        actual = sha256_path(ROOT / relative)
        if actual != expected:
            raise ValueError(f"Candidate hash differs for {name}: {actual}")
    helper = ROOT / HELPER_PATH
    if sha256_path(helper) != HELPER_SHA256:
        raise ValueError("Helper hash differs")
    with ZipFile(baseline) as source:
        infos = source.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)) or HELPER_NAME in names:
            raise ValueError("Baseline archive names differ")
        missing = set(sources) - set(names)
        if missing:
            raise ValueError(f"Baseline entries missing: {sorted(missing)}")
        baseline_entries = {
            info.filename: {"crc": info.CRC, "size": info.file_size}
            for info in infos
        }
        with ZipFile(partial, "w", allowZip64=True) as target:
            target.comment = source.comment
            for info in infos:
                replacement = sources.get(info.filename)
                origin = replacement.open("rb") if replacement else source.open(info)
                with origin, target.open(info, "w", force_zip64=True) as destination:
                    shutil.copyfileobj(origin, destination, 1024 * 1024)
            helper_info = ZipInfo.from_file(helper, HELPER_NAME)
            helper_info.compress_type = ZIP_DEFLATED
            with helper.open("rb") as origin, target.open(helper_info, "w") as destination:
                shutil.copyfileobj(origin, destination, 1024 * 1024)
    with ZipFile(partial) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"Archive CRC failed: {bad}")
        names = archive.namelist()
        if len(names) != len(baseline_entries) + 1 or len(names) != len(set(names)):
            raise ValueError("Output archive inventory differs")
        for name, source_path in sources.items():
            with archive.open(name) as stream:
                actual = sha256_stream(stream)
            if actual != sha256_path(source_path):
                raise ValueError(f"Archived replacement differs: {name}")
        with archive.open(HELPER_NAME) as stream:
            if sha256_stream(stream) != HELPER_SHA256:
                raise ValueError("Archived helper differs")
        for info in archive.infolist():
            if info.filename == HELPER_NAME:
                continue
            original = baseline_entries[info.filename]
            if info.filename in sources:
                continue
            if info.CRC != original["crc"] or info.file_size != original["size"]:
                raise ValueError(f"Unchanged entry differs: {info.filename}")
    partial.replace(output)
    report = {
        "version": "v1.3.3",
        "archive": output.name,
        "archive_size": output.stat().st_size,
        "archive_sha256": sha256_path(output),
        "entries": len(names),
        "baseline_entries": len(baseline_entries),
        "crc_verified": True,
        "unchanged_entries_verified": len(names) - len(sources) - 1,
        "replacements": {
            name: {"source": relative, "sha256": expected}
            for name, (relative, expected) in REPLACEMENTS.items()
        },
        "added": {HELPER_NAME: {"source": HELPER_PATH, "sha256": HELPER_SHA256}},
    }
    report_path = ROOT / ".work/final/release-manifest.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RELEASE_ARCHIVE_VERIFIED", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
