using TMPro;
using UnityEngine;

public static class ArabicOutlineFix
{
    private static readonly Color OutlineColor = new Color(1f, 0.55f, 0.72f, 1f);
    private const float OutlineWidth = 0.18f;

    public static void ApplyDialogue(TextMeshProUGUI text)
    {
        if (IsArabic(text))
        {
            ConfigureDialogue(text);
        }
    }

    public static void ApplyDialogueName(TextMeshProUGUI text)
    {
        if (IsArabic(text))
        {
            text.color = Color.white;
            text.faceColor = Color.white;
            text.outlineColor = OutlineColor;
            text.outlineWidth = 0.12f;
            Material material = text.fontSharedMaterial;
            if (material == null)
            {
                return;
            }
            material.EnableKeyword("OUTLINE_ON");
            material.SetFloat("_OutlineWidth", 0.12f);
            material.SetFloat("_OutlineSoftness", 0.0f);
            material.SetColor("_OutlineColor", OutlineColor);
            material.SetColor("_FaceColor", Color.white);
            text.SetMaterialDirty();
        }
    }

    private static void ConfigureDialogue(TextMeshProUGUI text)
    {
        text.color = Color.white;
        text.faceColor = Color.white;
        text.outlineColor = Color.white;
        text.outlineWidth = 0.0f;
        Material material = text.fontSharedMaterial;
        if (material == null)
        {
            return;
        }
        material.DisableKeyword("OUTLINE_ON");
        material.SetFloat("_OutlineWidth", 0.0f);
        material.SetFloat("_OutlineSoftness", 0.0f);
        material.SetColor("_OutlineColor", Color.white);
        material.SetColor("_FaceColor", Color.white);
        text.SetMaterialDirty();
    }

    public static void ApplySettings(RenpyPreferencesMenuUI menu)
    {
        foreach (TextMeshProUGUI text in menu.GetComponentsInChildren<TextMeshProUGUI>(true))
        {
            if (IsArabic(text))
            {
                Configure(text, true);
            }
        }
    }

    public static bool TryApplyInteractive(TextMeshProUGUI text)
    {
        if (!IsArabic(text))
        {
            return false;
        }
        RenpyOutlinesUI controller = text.GetComponent<RenpyOutlinesUI>();
        if (controller != null)
        {
            controller.ResetStructure();
        }
        Configure(text, false);
        return true;
    }

    private static void Configure(TextMeshProUGUI text, bool white)
    {
        if (white)
        {
            text.color = Color.white;
            text.faceColor = Color.white;
        }
        text.outlineColor = OutlineColor;
        text.outlineWidth = OutlineWidth;
        Material material = text.fontSharedMaterial;
        if (material == null)
        {
            return;
        }
        material.EnableKeyword("OUTLINE_ON");
        material.SetFloat("_OutlineWidth", OutlineWidth);
        material.SetFloat("_OutlineSoftness", 0.0f);
        material.SetColor("_OutlineColor", OutlineColor);
        material.SetColor("_FaceColor", Color.white);
        text.SetMaterialDirty();
    }

    private static bool IsArabic(TextMeshProUGUI text)
    {
        if (text == null)
        {
            return false;
        }
        if (text.text != null)
        {
            foreach (char character in text.text)
            {
                if (IsArabicCharacter(character))
                {
                    return true;
                }
            }
        }
        TMP_TextInfo info = text.textInfo;
        if (info != null)
        {
            for (int i = 0; i < info.characterCount && i < info.characterInfo.Length; i++)
            {
                if (IsArabicCharacter(info.characterInfo[i].character))
                {
                    return true;
                }
            }
        }
        return false;
    }

    private static bool IsArabicCharacter(char character)
    {
        return (character >= '\u0600' && character <= '\u06ff') ||
            (character >= '\ufb50' && character <= '\ufeff');
    }
}
