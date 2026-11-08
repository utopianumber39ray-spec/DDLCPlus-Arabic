# تعريب Doki Doki Literature Club Plus — Arabic Localization

<div dir="rtl">

**تعريب كامل للعبة Doki Doki Literature Club Plus إلى العربية الفصحى** — الواجهة، القوائم، الحوارات، القصص الجانبية (Side Stories)، وكل مراحل اللعبة.

</div>

> Fan-made Arabic localization patch for **Doki Doki Literature Club Plus** (Windows / Steam).
> The patch does not contain the game itself. You must own the original game.

---

## المحتوى / What is included

| الملف / File | الوصف |
|---|---|
| `install.bat` / `install.ps1` | مثبّت بضغطة واحدة (ينسخ الملفات ويحتفظ بنسخة احتياطية) |
| `restore.bat` / `restore.ps1` | استعادة الملفات الأصلية وإزالة التعريب |
| `files/` | ملفات التعريب (حزم النصوص والخطوط) |
| `SHA256SUMS.txt` | بصمات الملفات للتحقق من سلامتها |

## المتطلبات / Requirements

- Windows 10/11 (64-bit)
- نسخة أصلية من اللعبة على Steam (نسخة الـ2021 الحالية)
- مساحة فارغة ~700 MB أثناء التثبيت (تُحفظ نسخة احتياطية للأصول الأصلية)

## التثبيت / Installation

<div dir="rtl">

1. أغلق اللعبة إن كانت تعمل.
2. فك ضغط الحزمة في أي مكان.
3. شغّل **`install.bat`** بنقرتين.
4. المثبّت يكتشف مجلد Steam تلقائيًا؛ إن لم يجدده ألصق المسار:
   `C:\Program Files (x86)\Steam\steamapps\common\Doki Doki Literature Club Plus`
5. شغّل اللعبة — **تفتح بالعربية تلقائيًا من أول تشغيل** (بدون أي تعديل يدوي).
   يمكنك تغيير اللغة في أي وقت من: **الإعدادات ← اللغة**.

</div>

## الإزالة / Uninstall

<div dir="rtl">

شغّل **`restore.bat`** — يعيد كل الملفات الأصلية من النسخة الاحتياطية `_DDLCPlus_Arabic_Backup` التي أُنشئت أثناء التثبيت.

</div>

## النسخة المختبرة / Tested build

- DDLC+ (Steam, Windows) — build 2021, Unity 2019.4.20f1.
- إذا حدّثت Steam اللعبة لاحقًا فقد يُعاد ضبط التعريب؛ أعد تشغيل `install.bat`.

## ملاحظات / Notes

- التعريب يغطي **16,174 سطرًا** في **226 مشهدًا**.
- الخطوط العربية مدمجة في أطالس اللعبة (TMP) — لا حاجة لتثبيت خطوط على النظام.
- **أسماء اللاعبين بالعربية مدعومة** (تُشكَّل وتُعرض متصلة بالاتجاه الصحيح).
- تبدأ اللعبة بالعربية حتى على ويندوز الإنجليزي (تعديل على `DDLC.dll` + `ArabicShaper.dll`).
- لا تُعدَّل أي أصول أخرى في اللعبة.
- هذه الحزمة تعديل (patch) فقط ولا تحتوي اللعبة.
- **للنسخة الكاملة الجاهزة (اللعبة + التعريب مدمجًا)** راجع صفحة الإصدارات (Releases) في المستودع.

## الترخيص / License

هذا تعريب من صنع المعجبين. حقوق اللعبة والنصوص الأصلية تعود إلى **Team Salvato**.
This is a fan translation. All rights to the original game and its script belong to **Team Salvato**.
