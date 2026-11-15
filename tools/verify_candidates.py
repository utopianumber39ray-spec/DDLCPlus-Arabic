import hashlib
import json
from pathlib import Path

import UnityPy
from PIL import ImageChops, ImageFont

import unity_support as support
from font_scope import FONT_SPECS, MATERIAL_IDS, OUTLINE_COLOR, OUTLINE_WIDTH
from make_candidates import FONT_DIR, FACTOR, render

ROOT = Path(__file__).resolve().parents[1]
TECH = ROOT / ".work/technical"
OUT = TECH / "candidate"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def properties(entries):
    result = {}
    for key, value in entries:
        if isinstance(key, dict):
            key = key.get("name", str(key))
        result[key] = value
    return result


def main():
    manifest = json.loads((OUT / "candidate_manifest.json").read_text(encoding="utf-8"))
    files = sorted({spec["file"] for spec in FONT_SPECS})
    baseline = support.configure_environment(UnityPy.load(*(str(support.DATA / name) for name in files), str(support.DATA / "globalgamemanagers.assets")))
    candidate = support.configure_environment(UnityPy.load(*(str(OUT / name) for name in files), str(support.DATA / "globalgamemanagers.assets")))
    baseline_objects = {(obj.assets_file.name, obj.path_id): obj for obj in baseline.objects}
    objects = {(obj.assets_file.name, obj.path_id): obj for obj in candidate.objects}
    font_records = []
    for spec in FONT_SPECS:
        filename, path_id = spec["file"], spec["path_id"]
        baseline_font = support.mono_tree(baseline_objects[(filename, path_id)])
        tree = support.mono_tree(objects[(filename, path_id)])
        old_chars = [(char["m_Unicode"], char["m_GlyphIndex"]) for char in baseline_font["m_CharacterTable"]]
        assert [(char["m_Unicode"], char["m_GlyphIndex"]) for char in tree["m_CharacterTable"]] == old_chars
        atlas_id = tree["m_AtlasTextures"][0]["m_PathID"]
        if spec["role"] == "dialogue_active_clear":
            assert (filename, path_id, atlas_id) == ("sharedassets1.assets", 1569, 72)
            assert tree["m_Name"] == "Aller_Rg SDF"
            assert tree["material"]["m_PathID"] == 41
            assert tree["m_AtlasPadding"] == 20
            assert spec["font_scale"] == 1.18 and spec["preserve_marks"] is True
        atlas_obj = objects[(filename, atlas_id)]
        old_image = baseline_objects[(filename, atlas_id)].read().image
        image = atlas_obj.read().image
        assert image.size == (tree["m_AtlasWidth"], tree["m_AtlasHeight"])
        assert image.getchannel("A").getextrema()[1] > 128
        if spec.get("restore_original"):
            assert tree == baseline_font
            assert image.tobytes() == old_image.tobytes()
            font_records.append({"file": filename, "font_path_id": path_id, "atlas_path_id": atlas_id, "atlas_size": list(image.size), "glyph_count": len(tree["m_GlyphTable"]), "role": spec["role"], "original_font_restored": True})
            continue
        old_glyphs = {glyph["m_Index"]: glyph for glyph in baseline_font["m_GlyphTable"]}
        glyphs = {glyph["m_Index"]: glyph for glyph in tree["m_GlyphTable"]}
        raster_font = ImageFont.truetype(str(FONT_DIR / spec["source_font"]), round(int(tree["m_FaceInfo"]["m_PointSize"]) * FACTOR * spec.get("font_scale", 1.0)))
        padding = int(tree["m_AtlasPadding"])
        for char in tree["m_CharacterTable"]:
            cp = char["m_Unicode"]
            glyph = glyphs[char["m_GlyphIndex"]]
            rect = glyph["m_GlyphRect"]
            assert rect["m_X"] >= 0 and rect["m_Y"] >= 0
            assert rect["m_X"] + rect["m_Width"] <= image.width
            assert rect["m_Y"] + rect["m_Height"] <= image.height
            if 0x0600 <= cp <= 0x06FF or 0xFB50 <= cp <= 0xFEFF:
                if rect["m_Width"] and rect["m_Height"]:
                    assert spec.get("preserve_sdf") or (spec.get("preserve_marks") and cp in {0x064B, 0x064C, 0x064D, 0x0651}) or glyph["m_Metrics"]["m_HorizontalAdvance"] > 0
                    box = (rect["m_X"], image.height - rect["m_Y"] - rect["m_Height"], rect["m_X"] + rect["m_Width"], image.height - rect["m_Y"])
                    actual = image.getchannel("A").crop(box)
                    if spec.get("preserve_marks") and cp in {0x064B, 0x064C, 0x064D, 0x0651}:
                        old_rect = old_glyphs[char["m_GlyphIndex"]]["m_GlyphRect"]
                        assert glyph["m_Metrics"] == old_glyphs[char["m_GlyphIndex"]]["m_Metrics"]
                        old_box = (old_rect["m_X"], old_image.height - old_rect["m_Y"] - old_rect["m_Height"], old_rect["m_X"] + old_rect["m_Width"], old_image.height - old_rect["m_Y"])
                        expected = old_image.getchannel("A").crop(old_box)
                    elif spec.get("preserve_sdf"):
                        old_rect = old_glyphs[char["m_GlyphIndex"]]["m_GlyphRect"]
                        assert glyph["m_Metrics"] == old_glyphs[char["m_GlyphIndex"]]["m_Metrics"]
                        old_box = (old_rect["m_X"], old_image.height - old_rect["m_Y"] - old_rect["m_Height"], old_rect["m_X"] + old_rect["m_Width"], old_image.height - old_rect["m_Y"])
                        expected = old_image.getchannel("A").crop(old_box)
                        assert rect["m_X"] >= padding and rect["m_Y"] >= padding
                        assert rect["m_X"] + rect["m_Width"] + padding <= image.width
                        assert rect["m_Y"] + rect["m_Height"] + padding <= image.height
                        alpha = image.getchannel("A")
                        margins = (
                            (box[0] - padding, box[1] - padding, box[2] + padding, box[1]),
                            (box[0] - padding, box[3], box[2] + padding, box[3] + padding),
                            (box[0] - padding, box[1], box[0], box[3]),
                            (box[2], box[1], box[2] + padding, box[3]),
                        )
                        assert all(alpha.crop(margin).getextrema() == (0, 0) for margin in margins), (filename, path_id, hex(cp))
                    else:
                        expected = render(raster_font, cp, padding)
                        assert expected is not None
                        assert (rect["m_Width"], rect["m_Height"]) == (expected["w"], expected["h"])
                        assert glyph["m_Metrics"] == expected["metrics"]
                        expected = expected["image"].getchannel("A").crop((padding, padding, padding + rect["m_Width"], padding + rect["m_Height"]))
                    assert actual.size == expected.size
                    assert ImageChops.difference(actual, expected).getbbox() is None, (filename, path_id, hex(cp))
            else:
                assert glyph["m_Metrics"] == old_glyphs[char["m_GlyphIndex"]]["m_Metrics"]
                old_rect = old_glyphs[char["m_GlyphIndex"]]["m_GlyphRect"]
                if rect["m_Width"] and rect["m_Height"]:
                    old_box = (old_rect["m_X"], old_image.height - old_rect["m_Y"] - old_rect["m_Height"], old_rect["m_X"] + old_rect["m_Width"], old_image.height - old_rect["m_Y"])
                    new_box = (rect["m_X"], image.height - rect["m_Y"] - rect["m_Height"], rect["m_X"] + rect["m_Width"], image.height - rect["m_Y"])
                    assert ImageChops.difference(old_image.getchannel("A").crop((old_rect["m_X"], old_image.height - old_rect["m_Y"] - old_rect["m_Height"], old_rect["m_X"] + old_rect["m_Width"], old_image.height - old_rect["m_Y"])), image.getchannel("A").crop((rect["m_X"], image.height - rect["m_Y"] - rect["m_Height"], rect["m_X"] + rect["m_Width"], image.height - rect["m_Y"]))).getbbox() is None, (filename, path_id, hex(cp))
        font_records.append({"file": filename, "font_path_id": path_id, "atlas_path_id": atlas_id, "atlas_size": list(image.size), "glyph_count": len(glyphs), "role": spec["role"], "sdf_pixels_preserved": spec.get("preserve_sdf", False), "font_scale": spec.get("font_scale", 1.0), "preserve_marks": spec.get("preserve_marks", False)})
    material_records = []
    for filename, ids in MATERIAL_IDS.items():
        for path_id in ids:
            tree = objects[(filename, path_id)].read_typetree()
            baseline_tree = baseline_objects[(filename, path_id)].read_typetree()
            saved = tree["m_SavedProperties"]
            floats = properties(saved["m_Floats"])
            colors = properties(saved["m_Colors"])
            baseline_floats = properties(baseline_tree["m_SavedProperties"]["m_Floats"])
            baseline_colors = properties(baseline_tree["m_SavedProperties"]["m_Colors"])
            is_dialogue = filename == "sharedassets1.assets" and path_id == 41
            is_name = filename == "sharedassets1.assets" and path_id == 48
            expected_width = 0.0 if is_dialogue else (0.12 if is_name else OUTLINE_WIDTH)
            expected_color = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0} if is_dialogue else OUTLINE_COLOR
            assert abs(floats["_OutlineWidth"] - expected_width) < 0.00001
            assert floats["_OutlineSoftness"] == 0.0
            assert all(abs(colors["_OutlineColor"][key] - value) < 0.00001 for key, value in expected_color.items())
            assert colors["_FaceColor"] == baseline_colors["_FaceColor"] == {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
            assert all(floats[key] == value for key, value in baseline_floats.items() if key not in ("_OutlineWidth", "_OutlineSoftness"))
            assert all(colors[key] == value for key, value in baseline_colors.items() if key != "_OutlineColor")
            keywords = set(tree.get("m_ShaderKeywords", "").split())
            baseline_keywords = set(baseline_tree.get("m_ShaderKeywords", "").split())
            assert ("OUTLINE_ON" not in keywords) if is_dialogue else ("OUTLINE_ON" in keywords)
            assert keywords ^ baseline_keywords <= {"OUTLINE_ON"}
            assert is_dialogue or baseline_keywords <= keywords
            assert tree["m_Shader"] == baseline_tree["m_Shader"]
            material_records.append({"file": filename, "path_id": path_id, "face_color": colors["_FaceColor"], "outline_color": colors["_OutlineColor"], "outline_width": floats["_OutlineWidth"], "shader_keywords": tree["m_ShaderKeywords"]})
    for filename in files:
        assert sha256(support.DATA / filename) == manifest["baseline_sha256"][filename]
    report = {"font_count": len(font_records), "material_count": len(material_records), "fonts": font_records, "materials": material_records}
    (TECH / "reports" / "candidate_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("CANDIDATE_ASSETS_VERIFIED")
    print("CANDIDATE_ROUNDTRIP_VERIFIED")


if __name__ == "__main__":
    main()
