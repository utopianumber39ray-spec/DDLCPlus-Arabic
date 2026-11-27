#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TECH="$ROOT/.work/technical"
PROJECT="$ROOT/tools/outline_fix"
ORIGINAL="$ROOT/.work/extracted/Doki Doki Literature Club Plus_Data/Managed"
OUTPUT="${OUTPUT:-$TECH/candidate_managed}"
NEXT="$OUTPUT.next"
if [ -x "$TECH/vendor/dotnet/dotnet" ]; then
    DOTNET="$TECH/vendor/dotnet/dotnet"
    export DOTNET_ROOT="$TECH/vendor/dotnet"
else
    DOTNET=$(command -v dotnet)
fi
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
[ "$(sha256sum "$ORIGINAL/DDLC.dll" | cut -d' ' -f1)" = "9b354df81e2903b7c7ac30a67e4af20d819ecba6971328c6d72239900ab49475" ]
[ ! -e "$OUTPUT" ] || { printf '%s\n' "Refusing to overwrite $OUTPUT" >&2; exit 2; }
[ ! -e "$NEXT" ] || { printf '%s\n' "Refusing to overwrite $NEXT" >&2; exit 2; }
"$DOTNET" build "$PROJECT/OutlineFix.csproj" -c Release --nologo
"$DOTNET" build "$PROJECT/PatchOutline.csproj" -c Release --nologo
mkdir "$NEXT"
for source in "$ORIGINAL"/*; do
    ln -s "$source" "$NEXT/$(basename "$source")"
done
rm "$NEXT/DDLC.dll" "$NEXT/TextTypewriterEffect.dll"
"$DOTNET" run --project "$PROJECT/PatchOutline.csproj" -c Release --no-build -- "$ORIGINAL/DDLC.dll" "$NEXT/DDLC.dll" "$ORIGINAL/TextTypewriterEffect.dll" "$NEXT/TextTypewriterEffect.dll"
cp "$PROJECT/bin/Release/netstandard2.0/ArabicOutlineFix.dll" "$NEXT/ArabicOutlineFix.dll"
"$TECH/vendor/dotnet-tools/ilspycmd" "$NEXT/ArabicOutlineFix.dll" -t ArabicOutlineFix -o "$TECH/reports"
"$TECH/vendor/dotnet-tools/ilspycmd" "$NEXT/DDLC.dll" -t RenpyOutlines > "$TECH/reports/RenpyOutlines.candidate.decompiled.cs"
"$TECH/vendor/dotnet-tools/ilspycmd" "$NEXT/DDLC.dll" -t RenpyOutlinesUI > "$TECH/reports/RenpyOutlinesUI.candidate.decompiled.cs"
"$TECH/vendor/dotnet-tools/ilspycmd" "$NEXT/DDLC.dll" -t RenpyWindowManager > "$TECH/reports/RenpyWindowManager.candidate.decompiled.cs"
"$TECH/vendor/dotnet-tools/ilspycmd" "$NEXT/DDLC.dll" -t RenpyPreferencesMenuUI > "$TECH/reports/RenpyPreferencesMenuUI.candidate.decompiled.cs"
"$TECH/vendor/dotnet-tools/ilspycmd" "$NEXT/DDLC.dll" -t RenpyHistoryMenuUI > "$TECH/reports/RenpyHistoryMenuUI.candidate.decompiled.cs"
"$TECH/vendor/dotnet-tools/ilspycmd" "$NEXT/TextTypewriterEffect.dll" -t TextTypewriterEffect.TextTypewriterEffect > "$TECH/reports/TextTypewriterEffect.candidate.decompiled.cs"
mv "$NEXT" "$OUTPUT"
python3 - "$ROOT" "$OUTPUT" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
output = Path(sys.argv[2])
original = root / ".work/extracted/Doki Doki Literature Club Plus_Data/Managed/DDLC.dll"
original_typewriter = root / ".work/extracted/Doki Doki Literature Club Plus_Data/Managed/TextTypewriterEffect.dll"
candidate = output / "DDLC.dll"
typewriter = output / "TextTypewriterEffect.dll"
helper = output / "ArabicOutlineFix.dll"
def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
report = {
    "schema": 1,
    "source": ".work/extracted/Doki Doki Literature Club Plus_Data/Managed/DDLC.dll",
    "source_sha256": sha256(original),
    "candidate": str(candidate.relative_to(root)),
    "candidate_sha256": sha256(candidate),
    "typewriter_source": str(original_typewriter.relative_to(root)),
    "typewriter_source_sha256": sha256(original_typewriter),
    "typewriter_candidate": str(typewriter.relative_to(root)),
    "typewriter_sha256": sha256(typewriter),
    "helper": str(helper.relative_to(root)),
    "helper_sha256": sha256(helper),
    "original_modified": False,
    "non_target_managed_files": "symbolic links to the original Managed directory",
    "hooks": [
        "RenpyOutlines.CreateOutlines(TextMeshProUGUI, RenpyOutlinesUI)",
        "RenpyOutlines.ApplySingleOutline(RenpyOutlineData, TextMeshProUGUI)",
        "RenpyOutlinesUI.SetOutlines(RenpyOutlines)",
        "RenpyWindowManager.Update()",
        "RenpyPreferencesMenuUI.Update()",
        "RenpyPreferencesMenuUI.OnHide()",
        "RenpyHistoryMenuUI.OnShow()",
        "TextTypewriterEffect.StartText(string, int, int, int, int, List<Tuple<int, float>>, float)",
    ],
    "arabic_dialogue_immediate": True,
    "arabic_ranges": ["0600-06FF", "FB50-FEFF"],
    "arabic_detection": ["text", "textInfo.characterInfo bounded by characterCount and array length"],
    "dialogue_component": "RenpyWindowManager.tte.text (TMPro.TextMeshProUGUI)",
    "dialogue_name_component": "RenpyWindowManager.whoText (TMPro.TextMeshProUGUI)",
    "settings_component": "RenpyPreferencesMenuUI children (TMPro.TextMeshProUGUI)",
    "settings_reset_hook": "RenpyPreferencesMenuUI.OnHide() -> ArabicOutlineFix.ResetSettings()",
    "settings_guard": "ApplySettings runs once per menu open; ResetSettings clears the guard on close",
    "history_arabic_only": True,
    "outline_rgba": [1.0, 0.55, 0.72, 1.0],
    "outline_width": 0.18,
    "dialogue_outline_width": 0.0,
    "dialogue_name_outline_width": 0.08,
    "interactive_outline_color": "HistoryColor (dark maroon)",
    "interactive_outline_width": 0.0,
    "runtime_material_replacement": False,
    "per_instance_material": True,
    "diagnostics_removed": True,
    "latin_path_preserved": True,
}
report_path = output / "managed_candidate.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("MANAGED_CANDIDATE_BUILT", report["candidate_sha256"], report["helper_sha256"])
PY
