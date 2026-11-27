import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TECH = ROOT / ".work/technical"
ORIGINAL = ROOT / ".work/extracted/Doki Doki Literature Club Plus_Data/Managed"
CANDIDATE = TECH / "candidate_managed"
EXPECTED_ORIGINAL = "9b354df81e2903b7c7ac30a67e4af20d819ecba6971328c6d72239900ab49475"
EXPECTED_HOOKS = [
    "RenpyOutlines.CreateOutlines(TextMeshProUGUI, RenpyOutlinesUI)",
    "RenpyOutlines.ApplySingleOutline(RenpyOutlineData, TextMeshProUGUI)",
    "RenpyOutlinesUI.SetOutlines(RenpyOutlines)",
    "RenpyWindowManager.Update()",
    "RenpyPreferencesMenuUI.Update()",
    "RenpyPreferencesMenuUI.OnHide()",
    "RenpyHistoryMenuUI.OnShow()",
    "TextTypewriterEffect.StartText(string, int, int, int, int, List<Tuple<int, float>>, float)",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decompiled(name):
    source = (TECH / "reports" / f"{name}.decompiled.cs").read_text(encoding="utf-8")
    assert "Error near IL" not in source
    return source


def main():
    report = json.loads((CANDIDATE / "managed_candidate.json").read_text(encoding="utf-8"))
    assert sha256(ORIGINAL / "DDLC.dll") == EXPECTED_ORIGINAL == report["source_sha256"]
    assert sha256(CANDIDATE / "DDLC.dll") == report["candidate_sha256"]
    assert sha256(CANDIDATE / "ArabicOutlineFix.dll") == report["helper_sha256"]
    assert sha256(ORIGINAL / "TextTypewriterEffect.dll") == report["typewriter_source_sha256"]
    assert sha256(CANDIDATE / "TextTypewriterEffect.dll") == report["typewriter_sha256"]
    assert report["arabic_dialogue_immediate"] is True
    assert report["original_modified"] is False
    assert report["latin_path_preserved"] is True
    assert report["outline_rgba"] == [1.0, 0.55, 0.72, 1.0]
    assert report["outline_width"] == 0.18
    assert report["dialogue_outline_width"] == 0.0
    assert report["dialogue_name_outline_width"] == 0.08
    assert report["runtime_material_replacement"] is False
    assert report["per_instance_material"] is True
    assert report["diagnostics_removed"] is True
    assert report["hooks"] == EXPECTED_HOOKS
    assert report["dialogue_component"] == "RenpyWindowManager.tte.text (TMPro.TextMeshProUGUI)"
    assert report["dialogue_name_component"] == "RenpyWindowManager.whoText (TMPro.TextMeshProUGUI)"
    assert report["settings_component"] == "RenpyPreferencesMenuUI children (TMPro.TextMeshProUGUI)"
    for source in ORIGINAL.iterdir():
        if source.name not in ("DDLC.dll", "TextTypewriterEffect.dll"):
            assert (CANDIDATE / source.name).is_symlink(), source.name
            assert (CANDIDATE / source.name).resolve() == source.resolve(), source.name

    outlines = decompiled("RenpyOutlines.candidate")
    assert outlines.count("ArabicOutlineFix.TryApplyInteractive(text)") == 2
    assert outlines.index("TryApplyInteractive(text)") < outlines.index("outlineController.ResetStructure()")
    assert "outlineController.AddNewOutline()" in outlines
    assert "float outlineWidth = outline.size / 10f;" in outlines
    assert "text.UpdateFontAsset();" in outlines

    controller = decompiled("RenpyOutlinesUI.candidate")
    assert "if (!ArabicOutlineFix.TryApplyInteractive(mainText))" in controller
    assert "ApplyOutlines();" in controller
    window = decompiled("RenpyWindowManager.candidate")
    assert "ArabicOutlineFix.ApplyDialogue(tte.text);" in window
    assert "ArabicOutlineFix.ApplyDialogueName(whoText);" in window
    preferences = decompiled("RenpyPreferencesMenuUI.candidate")
    assert "ArabicOutlineFix.ApplySettings(this);" in preferences
    history = decompiled("RenpyHistoryMenuUI.candidate")
    assert "ArabicOutlineFix.ApplyHistory(this);" in history

    typewriter = decompiled("TextTypewriterEffect.candidate")
    assert "if (!ArabicOutlineFix.TryShowDialogueImmediately(this, newText, autoForwardTime))" in typewriter
    assert typewriter.index("TryShowDialogueImmediately(this, newText, autoForwardTime)") < typewriter.index("t1.Clear();")
    helper = decompiled("ArabicOutlineFix")
    assert "public static bool ShouldShowImmediately(string value)" in helper
    assert "public static bool TryShowDialogueImmediately(object target, string newText, float autoForwardTime)" in helper
    assert 'GetMethod("SetTextImmediate")' in helper
    assert ".maxVisibleCharacters = int.MaxValue;" in helper
    assert ".SetText(newText);" in helper
    assert ".ForceMeshUpdate();" in helper
    assert helper.index(".ForceMeshUpdate();") < helper.index('GetMethod("Rewrap")')
    assert "public static void ApplyDialogue(TextMeshProUGUI text)" in helper
    assert "public static void ApplyDialogueName(TextMeshProUGUI text)" in helper
    assert "dialogueNameText != text" in helper
    assert 'text.text == "ﺎﻜﻴﻧﻮﻣ"' in helper
    assert "dialogueNameBaseline + (flag ? 3f" in helper
    assert "text.enableAutoSizing = true;" in helper
    assert "text.fontSizeMin = 14f;" in helper
    assert "public static void ApplySettings(RenpyPreferencesMenuUI menu)" in helper
    assert "public static void ResetSettings()" in helper
    assert "public static void ApplyHistory(RenpyHistoryMenuUI menu)" in helper
    assert "HistoryColor" in helper
    assert "public static bool TryApplyInteractive(TextMeshProUGUI text)" in helper
    assert "ApplyHistory(componentInParent);" in helper
    assert "text.faceColor = Color.white;" in helper
    assert 'EnableKeyword("OUTLINE_ON")' in helper
    assert 'SetFloat("_OutlineWidth", 0.18f)' in helper
    assert 'SetFloat("_OutlineWidth", 0.08f)' in helper
    assert 'DisableKeyword("OUTLINE_ON")' in helper
    assert 'SetColor("_OutlineColor", OutlineColor)' in helper
    assert "textInfo.characterInfo[j].character" in helper
    assert "j < textInfo.characterInfo.Length" in helper
    assert "component.ResetStructure();" in helper
    assert "text.SetMaterialDirty();" in helper
    # Verify per-instance material usage (fontMaterial, not fontSharedMaterial)
    assert "fontMaterial" in helper
    assert "fontSharedMaterial" not in helper
    for removed in ("Debug.Log", "Diagnose", "TextSnapshots", "AODIAG", "Resources.FindObjectsOfTypeAll", "fontMaterial =", "fontMaterials ="):
        assert removed not in helper, removed
    for injected in (outlines, controller, window, preferences):
        assert "Diagnose" not in injected and "AODIAG" not in injected
    print("MANAGED_CANDIDATE_VERIFIED")


if __name__ == "__main__":
    main()
