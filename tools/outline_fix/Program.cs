using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

if (args.Length != 2)
{
    throw new ArgumentException("Usage: PatchOutline <original-DDLC.dll> <candidate-DDLC.dll>");
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

    module.Write(args[1]);
}
Console.WriteLine("ARABIC_OUTLINE_HOOK_INSTALLED");
