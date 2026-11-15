using System;
using TMPro;
using UnityEngine;

public static class ArabicOutlineFix
{
    private static readonly Color OutlineColor = new Color(1f, 0.55f, 0.72f, 1f);
    private const float OutlineWidth = 0.18f;
    private static TextMeshProUGUI dialogueNameText;
    private static float dialogueNameBaseline;

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
            if (dialogueNameText != text)
            {
                dialogueNameText = text;
                dialogueNameBaseline = text.rectTransform.anchoredPosition.y;
            }
            Vector2 position = text.rectTransform.anchoredPosition;
            position.y = dialogueNameBaseline + (text.text == "ﺎﻜﻴﻧﻮﻣ" ? 2f : 5f);
            text.rectTransform.anchoredPosition = position;
            text.color = Color.white;
            text.faceColor = Color.white;
            text.outlineColor = OutlineColor;
            text.outlineWidth = 0.08f;
            Material material = text.fontSharedMaterial;
            if (material == null)
            {
                return;
            }
            material.EnableKeyword("OUTLINE_ON");
            material.SetFloat("_OutlineWidth", 0.08f);
            material.SetFloat("_OutlineSoftness", 0.0f);
            material.SetColor("_OutlineColor", OutlineColor);
            material.SetColor("_FaceColor", Color.white);
            text.SetMaterialDirty();
        }
    }

    public static bool ShouldShowImmediately(string value)
    {
        if (value == null)
        {
            return false;
        }
        foreach (char character in value)
        {
            if (IsArabicCharacter(character))
            {
                return true;
            }
        }
        return false;
    }

    public static bool TryShowDialogueImmediately(object target, string newText, float autoForwardTime)
    {
        if (!ShouldShowImmediately(newText))
        {
            return false;
        }
        Type type = target.GetType();
        TextMeshProUGUI text = (TextMeshProUGUI)type.GetField("text").GetValue(target);
        text.maxVisibleCharacters = int.MaxValue;
        text.SetText(newText);
        text.ForceMeshUpdate();
        Type textFlow = Type.GetType("DDLCArabic.TextFlow, ArabicShaper", true);
        object wrapped = textFlow.GetMethod("Rewrap").Invoke(null, new object[] { text, newText });
        type.GetField("t2", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).SetValue(target, wrapped);
        type.GetProperty("AutoForwardTime").SetValue(target, autoForwardTime, null);
        type.GetMethod("SetTextImmediate").Invoke(target, new[] { wrapped });
        return true;
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
