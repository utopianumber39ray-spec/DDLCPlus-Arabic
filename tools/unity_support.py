from pathlib import Path

import UnityPy
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

ROOT = Path(__file__).resolve().parents[1]
TECH = ROOT / ".work/technical"
DATA = ROOT / ".work" / "extracted" / "Doki Doki Literature Club Plus_Data"
TypeTreeHelper.read_typetree_boost = None

_generator = None
_generator_version = None


def configure_environment(env):
    if not hasattr(env, "typetree_generator") or env.typetree_generator is None:
        generator = TypeTreeGenerator(env.objects[0].assets_file.unity_version)
        generator.load_local_dll_folder(str(DATA / "Managed"))
        env.typetree_generator = generator
    return env


def mono_node(obj):
    node = obj.generate_monobehaviour_node()
    for child in node.m_Children:
        if child.m_Name == "m_Enabled":
            child.m_MetaFlag = (child.m_MetaFlag or 0) | 0x4000
    return node


def mono_tree(obj):
    return obj.read_typetree(nodes=mono_node(obj))


def mono_node_for(obj):
    node = obj._get_typetree_node()
    for child in node.m_Children:
        if child.m_Name == "m_Enabled":
            child.m_MetaFlag = (child.m_MetaFlag or 0) | 0x4000
    return node


def class_name(obj):
    head = obj.parse_monobehaviour_head()
    script = head.m_Script.deref_parse_as_object()
    namespace = script.m_Namespace
    return f"{script.m_Namespace}.{script.m_ClassName}" if script.m_Namespace else script.m_ClassName
