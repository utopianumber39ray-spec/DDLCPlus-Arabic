import hashlib
import json
from pathlib import Path

import numpy as np
import UnityPy
from PIL import Image, ImageFont, ImageOps
from fontTools.ttLib import TTFont
from scipy.ndimage import distance_transform_edt

import unity_support as support
from font_scope import FONT_SPECS, MATERIAL_IDS, OUTLINE_COLOR, OUTLINE_WIDTH

ROOT = Path(__file__).resolve().parents[1]
TECH = ROOT / ".work/technical"
OUT = TECH / "candidate"
FONT_DIR = Path("/usr/share/fonts/truetype/noto")
FACTOR = 4


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def set_property(entries, name, value):
    for index, (key, old_value) in enumerate(entries):
        key_name = key.get("name") if isinstance(key, dict) else key
        if key_name == name:
            entries[index] = (key, value)
            return
    entries.append((name, value))


def render(font, cp, padding):
    is_mark = cp in {0x064B, 0x064C, 0x064D, 0x0651}
    if is_mark:
        font = ImageFont.truetype(font.path, font.size, layout_engine=ImageFont.Layout.BASIC)
    mask, offset = font.getmask2(chr(cp), anchor="ls")
    mask_width, mask_height = mask.size
    if not mask_width or not mask_height or mask.getbbox() is None:
        return None
    source = Image.frombytes("L", mask.size, bytes(mask))
    if is_mark:
        bounds = source.getbbox()
        source = source.crop(bounds)
        offset = (offset[0] + bounds[0], offset[1] + bounds[1])
        mask_width, mask_height = source.size
    spread = FACTOR * padding
    padded = Image.new("L", (mask_width + 2 * spread, mask_height + 2 * spread))
    padded.paste(source, (spread, spread))
    binary = np.asarray(padded) >= 128
    signed = (distance_transform_edt(binary) - distance_transform_edt(~binary)) / FACTOR
    width, height = (mask_width + FACTOR - 1) // FACTOR, (mask_height + FACTOR - 1) // FACTOR
    low = Image.fromarray(signed.astype("float32"), mode="F").resize(
        (width + 2 * padding, height + 2 * padding), Image.Resampling.BICUBIC
    )
    encoded = np.clip(128.0 + np.asarray(low) * 127.0 / padding, 0, 255).round().astype(np.uint8)
    alpha = Image.fromarray(encoded, "L")
    image = Image.new("RGBA", alpha.size)
    image.putalpha(alpha)
    return {
        "w": width,
        "h": height,
        "image": image,
        "metrics": {
            "m_Width": float(width),
            "m_Height": float(height),
            "m_HorizontalBearingX": offset[0] / FACTOR,
            "m_HorizontalBearingY": -offset[1] / FACTOR,
            "m_HorizontalAdvance": 0.0 if is_mark else font.getlength(chr(cp)) / FACTOR,
        },
    }


def pack(glyphs, replacements, original, padding, width, isolate_original=False):
    items = []
    for glyph in glyphs:
        old = glyph["m_GlyphRect"]
        replacement = replacements.get(glyph["m_Index"])
        w, h = (replacement["w"], replacement["h"]) if replacement else (old["m_Width"], old["m_Height"])
        if w and h:
            items.append({"id": glyph["m_Index"], "w": w, "h": h, "old": dict(old), "new": replacement})
    x = y = row_h = 0
    placed = []
    for item in sorted(items, key=lambda item: (-item["h"], -item["w"], item["id"])):
        patch_w, patch_h = item["w"] + 2 * padding, item["h"] + 2 * padding
        if patch_w > width:
            raise RuntimeError(f"Glyph {item['id']} wider than atlas")
        if x and x + patch_w > width:
            x = 0
            y += row_h + padding
            row_h = 0
        item.update(x=x, y=y)
        placed.append(item)
        x += patch_w + padding
        row_h = max(row_h, patch_h)
    height = max(64, ((y + row_h + 63) // 64) * 64)
    atlas = Image.new("RGBA", (width, height))
    padded_original = ImageOps.expand(original, border=padding)
    for item in placed:
        if item["new"] is None:
            old = item["old"]
            old_box = (
                old["m_X"],
                original.height - old["m_Y"] - old["m_Height"],
                old["m_X"] + old["m_Width"],
                original.height - old["m_Y"],
            )
            if isolate_original:
                patch = Image.new("RGBA", (item["w"] + 2 * padding, item["h"] + 2 * padding))
                patch.paste(original.crop(old_box), (padding, padding))
            else:
                patch = padded_original.crop((
                    old_box[0],
                    old_box[1],
                    old_box[0] + old["m_Width"] + 2 * padding,
                    old_box[1] + old["m_Height"] + 2 * padding,
                ))
        else:
            patch = item["new"]["image"]
        atlas.paste(patch, (item["x"], height - item["y"] - patch.height))
        item["rect"] = {
            "m_X": item["x"] + padding,
            "m_Y": item["y"] + padding,
            "m_Width": item["w"],
            "m_Height": item["h"],
        }
    return atlas, {item["id"]: item for item in placed}


def main():
    if OUT.exists():
        raise RuntimeError(f"Refusing to overwrite {OUT}")
    OUT.mkdir()
    files = sorted({spec["file"] for spec in FONT_SPECS})
    env = support.configure_environment(UnityPy.load(*(str(support.DATA / name) for name in files)))
    objects = {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}
    manifest = {"fonts": [], "materials": [], "method": "Dialogue: Noto Sans Arabic Bold at 1.18 scale, white fill with no outline; character names and linked settings: Noto Sans Arabic Bold at 0.66 scale with proportionally rendered marks and a thin light-pink outline; settings and interface outline materials preserved"}
    for spec in FONT_SPECS:
        filename, path_id = spec["file"], spec["path_id"]
        font_obj = objects[(filename, path_id)]
        tree = support.mono_tree(font_obj)
        atlas_id = tree["m_AtlasTextures"][0]["m_PathID"]
        atlas_obj = objects[(filename, atlas_id)]
        if spec.get("restore_original"):
            arabic = {char["m_Unicode"] for char in tree["m_CharacterTable"] if 0x0600 <= char["m_Unicode"] <= 0x06FF or 0xFB50 <= char["m_Unicode"] <= 0xFEFF}
            manifest["fonts"].append({
                "file": filename, "path_id": path_id, "atlas_path_id": atlas_id,
                "source_font": spec["source_font"], "source_font_sha256": sha256(FONT_DIR / spec["source_font"]),
                "atlas_size": list(atlas_obj.read().image.size), "arabic_characters": len(arabic),
                "replaced_glyphs": 0, "total_glyphs": len(tree["m_GlyphTable"]),
                "original_font_restored": True,
            })
            continue
        font = ImageFont.truetype(str(FONT_DIR / spec["source_font"]), round(int(tree["m_FaceInfo"]["m_PointSize"]) * FACTOR * spec.get("font_scale", 1.0)))
        cmap = TTFont(FONT_DIR / spec["source_font"]).getBestCmap()
        padding = int(tree["m_AtlasPadding"])
        replacements = {}
        arabic = set()
        for char in tree["m_CharacterTable"]:
            cp = char["m_Unicode"]
            if not (0x0600 <= cp <= 0x06FF or 0xFB50 <= cp <= 0xFEFF):
                continue
            arabic.add(cp)
            if spec.get("preserve_sdf") or (spec.get("preserve_marks") and cp in {0x061C, 0x064B, 0x064C, 0x064D, 0x0651}):
                continue
            if cp not in cmap:
                raise RuntimeError(f"Missing U+{cp:04X} in {spec['source_font']}")
            gid = char["m_GlyphIndex"]
            if gid not in replacements:
                rendered = render(font, cp, padding)
                if rendered is not None:
                    replacements[gid] = rendered
        atlas, placements = pack(tree["m_GlyphTable"], replacements, atlas_obj.read().image, padding, int(tree["m_AtlasWidth"]), isolate_original=spec.get("preserve_sdf", False))
        for glyph in tree["m_GlyphTable"]:
            placement = placements.get(glyph["m_Index"])
            if placement is None:
                continue
            glyph["m_GlyphRect"] = dict(placement["rect"])
            if placement["new"] is not None:
                glyph["m_Metrics"] = dict(placement["new"]["metrics"])
        tree["m_AtlasWidth"], tree["m_AtlasHeight"] = atlas.size
        tree["m_UsedGlyphRects"] = [dict(g["m_GlyphRect"]) for g in tree["m_GlyphTable"] if g["m_GlyphRect"]["m_Width"] and g["m_GlyphRect"]["m_Height"]]
        tree["m_FreeGlyphRects"] = []
        font_obj.save_typetree(tree, nodes=support.mono_node_for(font_obj))
        texture = atlas_obj.read()
        texture.image = atlas
        texture.m_Width, texture.m_Height = atlas.size
        texture.save()
        manifest["fonts"].append({
            "file": filename, "path_id": path_id, "atlas_path_id": atlas_id,
            "source_font": spec["source_font"], "source_font_sha256": sha256(FONT_DIR / spec["source_font"]),
            "atlas_size": atlas.size, "arabic_characters": len(arabic),
            "replaced_glyphs": len(replacements), "total_glyphs": len(tree["m_GlyphTable"]),
            "font_scale": spec.get("font_scale", 1.0), "preserve_marks": spec.get("preserve_marks", False),
        })
    for filename, ids in MATERIAL_IDS.items():
        for path_id in ids:
            obj = objects[(filename, path_id)]
            tree = obj.read_typetree()
            saved = tree["m_SavedProperties"]
            is_dialogue = filename == "sharedassets1.assets" and path_id == 41
            outline_width = 0.0 if is_dialogue else (0.08 if filename == "sharedassets1.assets" and path_id == 48 else OUTLINE_WIDTH)
            outline_color = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0} if is_dialogue else dict(OUTLINE_COLOR)
            set_property(saved["m_Floats"], "_OutlineWidth", outline_width)
            set_property(saved["m_Floats"], "_OutlineSoftness", 0.0)
            set_property(saved["m_Colors"], "_OutlineColor", outline_color)
            set_property(saved["m_Colors"], "_FaceColor", {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
            keywords = set(tree.get("m_ShaderKeywords", "").split())
            if is_dialogue:
                keywords.discard("OUTLINE_ON")
            else:
                keywords.add("OUTLINE_ON")
            tree["m_ShaderKeywords"] = " ".join(sorted(keywords))
            obj.save_typetree(tree)
            manifest["materials"].append({"file": filename, "path_id": path_id, "outline_color": outline_color, "outline_width": outline_width, "shader_keywords": tree["m_ShaderKeywords"]})
    for filename in files:
        assets_file = next(obj.assets_file for obj in env.objects if obj.assets_file.name == filename)
        (OUT / filename).write_bytes(assets_file.save())
    manifest["baseline_sha256"] = {filename: sha256(support.DATA / filename) for filename in files}
    manifest["candidate_sha256"] = {filename: sha256(OUT / filename) for filename in files}
    manifest["material_roles"] = {
        "dialogue_body": {"sharedassets1.assets": [41]},
        "dialogue_name": {"sharedassets1.assets": [48]},
        "settings": {"sharedassets1.assets": [52], "resources.assets": [11, 19]},
        "interaction_shadow_fix": {
            "managed_helper": "candidate_managed/ArabicOutlineFix.dll",
            "scope": "Arabic text only; one TMP outline instead of offset text clones",
            "material_18_underlay_preserved": True,
        },
    }
    (OUT / "candidate_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("CANDIDATE_ASSETS_BUILT", len(manifest["fonts"]), len(manifest["materials"]))


if __name__ == "__main__":
    main()
