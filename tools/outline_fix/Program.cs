using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

if (args.Length != 4)
{
    throw new ArgumentException("Usage: PatchOutline <original-DDLC.dll> <candidate-DDLC.dll> <original-TextTypewriterEffect.dll> <candidate-TextTypewriterEffect.dll>");
}

var resolver = new DefaultAssemblyResolver();
resolver.AddSearchDirectory(Path.GetDirectoryName(Path.GetFullPath(args[0])));
var parameters = new ReaderParameters { AssemblyResolver = resolver };
using (var module = ModuleDefinition.ReadModule(args[0], parameters))
{
    if (module.Types.Any(type => type.FullName == "ArabicOutlineFix"))
    {
        throw new InvalidDataException("The input already contains ArabicOutlineFix.");
    }
    var outlines = module.Types.Single(type => type.FullName == "RenpyOutlines");
    var helperAssembly = new AssemblyNameReference("ArabicOutlineFix", new Version(1, 0, 0, 0));
    module.AssemblyReferences.Add(helperAssembly);
    var helperType = new TypeReference("", "ArabicOutlineFix", module, helperAssembly);
    var textAssembly = module.AssemblyReferences.Single(item => item.Name == "Unity.TextMeshPro");
    var textType = new TypeReference("TMPro", "TextMeshProUGUI", module, textAssembly);
    var applyInteractive = new MethodReference("TryApplyInteractive", module.TypeSystem.Boolean, helperType);
    applyInteractive.Parameters.Add(new ParameterDefinition(textType));

    void InsertGuard(MethodDefinition method, Func<Instruction> loadText)
    {
        var processor = method.Body.GetILProcessor();
        var first = processor.Body.Instructions[0];
        processor.InsertBefore(first, loadText());
        processor.InsertBefore(first, processor.Create(OpCodes.Call, applyInteractive));
        processor.InsertBefore(first, processor.Create(OpCodes.Brfalse, first));
        processor.InsertBefore(first, processor.Create(OpCodes.Ret));
    }

    InsertGuard(outlines.Methods.Single(item => item.Name == "CreateOutlines"),
        () => outlines.Methods.Single(item => item.Name == "CreateOutlines").Body.GetILProcessor().Create(OpCodes.Ldarg_1));
    InsertGuard(outlines.Methods.Single(item => item.Name == "ApplySingleOutline"),
        () => outlines.Methods.Single(item => item.Name == "ApplySingleOutline").Body.GetILProcessor().Create(OpCodes.Ldarg_2));
    var outlineController = module.Types.Single(type => type.FullName == "RenpyOutlinesUI");
    var mainText = outlineController.Fields.Single(field => field.Name == "mainText");
    var processor = outlineController.Methods.Single(item => item.Name == "SetOutlines").Body.GetILProcessor();
    var first = processor.Body.Instructions[0];
    processor.InsertBefore(first, processor.Create(OpCodes.Ldarg_0));
    processor.InsertBefore(first, processor.Create(OpCodes.Ldfld, mainText));
    processor.InsertBefore(first, processor.Create(OpCodes.Call, applyInteractive));
    processor.InsertBefore(first, processor.Create(OpCodes.Brfalse, first));
    processor.InsertBefore(first, processor.Create(OpCodes.Ret));

    var windowManager = module.Types.Single(type => type.FullName == "RenpyWindowManager");
    var typewriter = windowManager.Fields.Single(field => field.Name == "tte");
    var typewriterText = typewriter.FieldType.Resolve().Fields.Single(field => field.Name == "text");
    var applyDialogue = new MethodReference("ApplyDialogue", module.TypeSystem.Void, helperType);
    applyDialogue.Parameters.Add(new ParameterDefinition(textType));
    var update = windowManager.Methods.Single(item => item.Name == "Update").Body;
    var updateProcessor = update.GetILProcessor();
    var updateFirst = update.Instructions[0];
    updateProcessor.InsertBefore(updateFirst, updateProcessor.Create(OpCodes.Ldarg_0));
    updateProcessor.InsertBefore(updateFirst, updateProcessor.Create(OpCodes.Ldfld, typewriter));
    updateProcessor.InsertBefore(updateFirst, updateProcessor.Create(OpCodes.Ldfld, module.ImportReference(typewriterText)));
    updateProcessor.InsertBefore(updateFirst, updateProcessor.Create(OpCodes.Call, applyDialogue));
    var whoText = windowManager.Fields.Single(field => field.Name == "whoText");
    var applyDialogueName = new MethodReference("ApplyDialogueName", module.TypeSystem.Void, helperType);
    applyDialogueName.Parameters.Add(new ParameterDefinition(textType));
    updateProcessor.InsertBefore(updateFirst, updateProcessor.Create(OpCodes.Ldarg_0));
    updateProcessor.InsertBefore(updateFirst, updateProcessor.Create(OpCodes.Ldfld, whoText));
    updateProcessor.InsertBefore(updateFirst, updateProcessor.Create(OpCodes.Call, applyDialogueName));

    var preferences = module.Types.Single(type => type.FullName == "RenpyPreferencesMenuUI");
    var applySettings = new MethodReference("ApplySettings", module.TypeSystem.Void, helperType);
    applySettings.Parameters.Add(new ParameterDefinition(preferences));
    var preferencesProcessor = preferences.Methods.Single(item => item.Name == "Update").Body.GetILProcessor();
    var preferencesFirst = preferencesProcessor.Body.Instructions[0];
    preferencesProcessor.InsertBefore(preferencesFirst, preferencesProcessor.Create(OpCodes.Ldarg_0));
    preferencesProcessor.InsertBefore(preferencesFirst, preferencesProcessor.Create(OpCodes.Call, applySettings));

    // Hook ResetSettings into OnHide (or Hide/Close) so the guard resets when
    // the settings menu is dismissed, allowing re-application on next open.
    var resetSettings = new MethodReference("ResetSettings", module.TypeSystem.Void, helperType);
    var hideMethod = preferences.Methods.FirstOrDefault(m => m.Name == "OnHide")
        ?? preferences.Methods.FirstOrDefault(m => m.Name == "Hide")
        ?? preferences.Methods.FirstOrDefault(m => m.Name == "Close");
    if (hideMethod != null)
    {
        var hideProcessor = hideMethod.Body.GetILProcessor();
        var hideFirst = hideMethod.Body.Instructions[0];
        hideProcessor.InsertBefore(hideFirst, hideProcessor.Create(OpCodes.Call, resetSettings));
    }

    var history = module.Types.Single(type => type.FullName == "RenpyHistoryMenuUI");
    var applyHistory = new MethodReference("ApplyHistory", module.TypeSystem.Void, helperType);
    applyHistory.Parameters.Add(new ParameterDefinition(history));
    var historyShow = history.Methods.Single(item => item.Name == "OnShow").Body;
    var historyProcessor = historyShow.GetILProcessor();
    foreach (var ret in historyShow.Instructions.Where(item => item.OpCode == OpCodes.Ret).ToArray())
    {
        historyProcessor.InsertBefore(ret, historyProcessor.Create(OpCodes.Ldarg_0));
        historyProcessor.InsertBefore(ret, historyProcessor.Create(OpCodes.Call, applyHistory));
    }

    module.Write(args[1]);
}
using (var module = ModuleDefinition.ReadModule(args[2], parameters))
{
    var helperAssembly = new AssemblyNameReference("ArabicOutlineFix", new Version(1, 0, 0, 0));
    module.AssemblyReferences.Add(helperAssembly);
    var helperType = new TypeReference("", "ArabicOutlineFix", module, helperAssembly);
    var typewriter = module.Types.Single(type => type.FullName == "TextTypewriterEffect.TextTypewriterEffect");
    var startText = typewriter.Methods.Single(method => method.Name == "StartText" && method.Parameters.Count == 7);
    var showImmediately = new MethodReference("TryShowDialogueImmediately", module.TypeSystem.Boolean, helperType);
    showImmediately.Parameters.Add(new ParameterDefinition(module.TypeSystem.Object));
    showImmediately.Parameters.Add(new ParameterDefinition(module.TypeSystem.String));
    showImmediately.Parameters.Add(new ParameterDefinition(module.TypeSystem.Single));
    var processor = startText.Body.GetILProcessor();
    var first = startText.Body.Instructions[0];
    processor.InsertBefore(first, processor.Create(OpCodes.Ldarg_0));
    processor.InsertBefore(first, processor.Create(OpCodes.Ldarg_1));
    processor.InsertBefore(first, processor.Create(OpCodes.Ldarg_S, startText.Parameters[6]));
    processor.InsertBefore(first, processor.Create(OpCodes.Call, showImmediately));
    processor.InsertBefore(first, processor.Create(OpCodes.Brfalse, first));
    processor.InsertBefore(first, processor.Create(OpCodes.Ret));
    module.Write(args[3]);
}
Console.WriteLine("ARABIC_OUTLINE_AND_TYPEWRITER_HOOKS_INSTALLED");
