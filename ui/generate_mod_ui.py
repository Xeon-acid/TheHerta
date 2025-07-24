import bpy

from ..utils.command_utils import *
from ..utils.timer_utils import TimerUtils
from ..utils.collection_utils import CollectionUtils
from ..generate_mod.m_counter import M_Counter

from ..mod_model.mod_unity_model import ModUnityModel
from ..mod_model.mod_hsr_model import ModHSRModel
from ..mod_model.mod_identityv_model import ModIdentityVModel
from ..mod_model.mod_yysls_model import ModCTXModel

from ..generate_mod.drawib_model_wwmi import DrawIBModelWWMI
from ..generate_mod.ini_model_wwmi import M_WWMIIniModel
    
# WWMI
class GenerateModWWMI(bpy.types.Operator):
    bl_idname = "herta.export_mod_wwmi"
    bl_label = "生成WWMI格式Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod WWMI")

        M_WWMIIniModel.initialzie()
        M_Counter.initialize()

        workspace_collection = bpy.context.collection

        result = CollectionUtils.is_valid_ssmt_workspace_collection(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}
        
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModelWWMI(draw_ib_collection)
            M_WWMIIniModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        M_WWMIIniModel.generate_unreal_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod WWMI")
        return {'FINISHED'}



class SSMTGenerateModUnityCSV2(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_unity_cs_v2"
    bl_label = "生成Mod(测试版)"
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

        migoto_mod_model = ModUnityModel(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityCS")
        return {'FINISHED'}
    

class SSMTGenerateModUnityVSV2(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_unity_vs_v2"
    bl_label = "生成Mod(测试版)"
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

        migoto_mod_model = ModUnityModel(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityVS")
        return {'FINISHED'}

class SSMTGenerateModHSRV3(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_hsr_v3"
    bl_label = "生成Mod(测试版)"
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

        migoto_mod_model = ModHSRModel(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod HSR V3")
        return {'FINISHED'}


class SSMTGenerateModIdentityVV2(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_identityv_v2"
    bl_label = "生成Mod(测试版)"
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

        migoto_mod_model = ModIdentityVModel(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod Mod V3")
        return {'FINISHED'}


class SSMTGenerateModYYSLSV2(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_yysls_v2"
    bl_label = "生成Mod(测试版)"
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

        migoto_mod_model = ModCTXModel(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod Mod V3")
        return {'FINISHED'}
    

class SSMTGenerateModWWMIV3(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod_wwmi_v3"
    bl_label = "生成Mod(测试版)"
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

        migoto_mod_model = ModCTXModel(workspace_collection=workspace_collection)
        migoto_mod_model.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod Mod V3")
        return {'FINISHED'}