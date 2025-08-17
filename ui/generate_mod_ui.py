import bpy

from ..utils.command_utils import *
from ..utils.timer_utils import TimerUtils
from ..utils.collection_utils import CollectionUtils
from ..generate_mod.m_counter import M_Counter

from ..mod_ini_generate.Unity import ModModelUnity
from ..mod_ini_generate.HonkaiStarRail import ModModelHonkaiStarRail
from ..mod_ini_generate.IdentityV import ModModelIdentityV
from ..mod_ini_generate.YYSLS import ModModelYYSLS
from ..mod_ini_generate.WWMI import ModModelWWMI




class SSMTGenerateModUnityCSV2(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_unity_cs_v2"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnityCS")

        M_Counter.initialize()

        # 先校验当前选中的工作空间是不是一个有效的工作空间集合
        workspace_collection = bpy.context.collection
        result = CollectionUtils.is_valid_ssmt_workspace_collection_v2(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}

        migoto_mod_model = ModModelUnity(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityCS")
        return {'FINISHED'}
    

class SSMTGenerateModUnityVSV2(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_unity_vs_v2"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnityVS")

        M_Counter.initialize()

        # 先校验当前选中的工作空间是不是一个有效的工作空间集合
        workspace_collection = bpy.context.collection
        result = CollectionUtils.is_valid_ssmt_workspace_collection_v2(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}

        migoto_mod_model = ModModelUnity(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityVS")
        return {'FINISHED'}

class SSMTGenerateModHSRV3(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_hsr_v3"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod HSR V3")

        M_Counter.initialize()

        # 先校验当前选中的工作空间是不是一个有效的工作空间集合
        workspace_collection = bpy.context.collection
        result = CollectionUtils.is_valid_ssmt_workspace_collection_v2(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}

        migoto_mod_model = ModModelHonkaiStarRail(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod HSR V3")
        return {'FINISHED'}


class SSMTGenerateModCTXMC(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_ctx_mc"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod Mod V3")

        M_Counter.initialize()

        # 先校验当前选中的工作空间是不是一个有效的工作空间集合
        workspace_collection = bpy.context.collection
        result = CollectionUtils.is_valid_ssmt_workspace_collection_v2(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}

        migoto_mod_model = ModModelIdentityV(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod Mod V3")
        return {'FINISHED'}


class SSMTGenerateModYYSLSV2(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_yysls_v2"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod Mod V3")

        M_Counter.initialize()

        # 先校验当前选中的工作空间是不是一个有效的工作空间集合
        workspace_collection = bpy.context.collection
        result = CollectionUtils.is_valid_ssmt_workspace_collection_v2(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}

        migoto_mod_model = ModModelYYSLS(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod Mod V3")
        return {'FINISHED'}
    

class SSMTGenerateModWWMIV3(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_wwmi_v3"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod Mod V3")

        M_Counter.initialize()

        # 先校验当前选中的工作空间是不是一个有效的工作空间集合
        workspace_collection = bpy.context.collection
        result = CollectionUtils.is_valid_ssmt_workspace_collection_v2(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}

        migoto_mod_model = ModModelWWMI(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unreal_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod Mod V3")
        return {'FINISHED'}