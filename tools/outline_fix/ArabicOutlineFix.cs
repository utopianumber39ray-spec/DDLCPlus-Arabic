using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

public static class ArabicOutlineFix
{
    private static readonly Color OutlineColor = new Color(1f, 0.55f, 0.72f, 1f);
    private static readonly Color HistoryColor = new Color(0.28f, 0.10f, 0.20f, 1f);
    private const float OutlineWidth = 0.18f;
    private static TextMeshProUGUI dialogueNameText;
    private static float dialogueNameBaseline;
    private static float dialogueNameFontSize;
    private static readonly HashSet<int> processedSettings = new HashSet<int>();
    private static bool settingsApplied;

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
                dialogueNameFontSize = text.fontSize;
            }
            string playerName = Renpy.CurrentContext.GetVariableString("player");
            bool isPlayerName = !string.IsNullOrEmpty(playerName) && text.text == playerName;
            if (isPlayerName)
            {
                text.enableAutoSizing = true;
                text.fontSizeMin = 14f;
                text.fontSizeMax = Mathf.Min(dialogueNameFontSize, 24f);
            }
            else
            {
                text.enableAutoSizing = false;
                text.fontSize = dialogueNameFontSize;
            }
            Vector2 position = text.rectTransform.anchoredPosition;
            position.y = dialogueNameBaseline + (isPlayerName ? 3f : (text.text == "ﺎﻜﻴﻧﻮﻣ" ? 2f : 5f));
            text.rectTransform.anchoredPosition = position;
            text.color = Color.white;
            text.faceColor = Color.white;
            text.outlineColor = OutlineColor;
            text.outlineWidth = 0.08f;
            // Use a per-instance material so we never mutate the shared material
            // that settings / other UI elements also reference.
            Material material = text.fontMaterial;
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
        // Per-instance material — do NOT touch the shared material.
        Material material = text.fontMaterial;
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
        // Only run once per menu open; skip if already applied to this instance.
        int id = menu.GetInstanceID();
        if (settingsApplied && processedSettings.Contains(id))
        {
            return;
        }
        processedSettings.Add(id);
        settingsApplied = true;
        foreach (TextMeshProUGUI text in menu.GetComponentsInChildren<TextMeshProUGUI>(true))
        {
            if (IsArabic(text))
            {
                Configure(text, true);
            }
        }
    }

    /// <summary>Called when the settings menu is closed so we re-apply on next open.</summary>
    public static void ResetSettings()
    {
        settingsApplied = false;
        processedSettings.Clear();
    }

    public static void ApplyHistory(RenpyHistoryMenuUI menu)
    {
        RenpyOutlinesUI controller = menu.HistoryText.GetComponent<RenpyOutlinesUI>();
        if (controller != null)
        {
            controller.ResetStructure();
        }
        menu.HistoryText.alignment = TextAlignmentOptions.TopRight;
        foreach (TextMeshProUGUI text in menu.HistoryText.transform.parent.GetComponentsInChildren<TextMeshProUGUI>(true))
        {
            if (!IsArabic(text))
            {
                continue;
            }
            text.color = HistoryColor;
            text.faceColor = HistoryColor;
            text.outlineWidth = 0.0f;
            // Per-instance material — avoid corrupting the shared material.
            Material material = text.fontMaterial;
            if (material != null)
            {
                material.DisableKeyword("OUTLINE_ON");
                material.SetFloat("_OutlineWidth", 0.0f);
                material.SetColor("_FaceColor", HistoryColor);
            }
            text.SetMaterialDirty();
        }
    }

    public static bool TryApplyInteractive(TextMeshProUGUI text)
    {
        if (!IsArabic(text))
        {
            return false;
        }
        RenpyHistoryMenuUI history = text.GetComponentInParent<RenpyHistoryMenuUI>();
        if (history != null)
        {
            ApplyHistory(history);
            return true;
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
        // Interactive (non-settings) texts use dark outline with zero width
        // to avoid distorted pink edges on the poem notebook.
        // Settings texts keep the pink outline for visual consistency.
        Color outlineColor = white ? OutlineColor : HistoryColor;
        float outlineWidth = white ? OutlineWidth : 0.0f;
        text.outlineColor = outlineColor;
        text.outlineWidth = outlineWidth;
        // Per-instance material — avoid corrupting the shared material that
        // dialogue and other UI elements also reference.
        Material material = text.fontMaterial;
        if (material == null)
        {
            return;
        }
        if (outlineWidth > 0f)
        {
            material.EnableKeyword("OUTLINE_ON");
        }
        else
        {
            material.DisableKeyword("OUTLINE_ON");
        }
        material.SetFloat("_OutlineWidth", outlineWidth);
        material.SetFloat("_OutlineSoftness", 0.0f);
        material.SetColor("_OutlineColor", outlineColor);
        material.SetColor("_FaceColor", white ? Color.white : HistoryColor);
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
