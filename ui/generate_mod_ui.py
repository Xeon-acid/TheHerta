import bpy

from ..utils.command_utils import *
from ..utils.timer_utils import TimerUtils
from ..utils.collection_utils import CollectionUtils
from ..utils.translate_utils import TR
from ..generate_mod.m_counter import M_Counter

from ..mod_ini_generate.Unity import ModModelUnity
from ..mod_ini_generate.HonkaiStarRail import ModModelHonkaiStarRail
from ..mod_ini_generate.IdentityV import ModModelIdentityV
from ..mod_ini_generate.YYSLS import ModModelYYSLS
from ..mod_ini_generate.WWMI import ModModelWWMI



class SSMTGenerateMod(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod"
    bl_label = TR.translate("生成Mod")
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod Mod")

        M_Counter.initialize()

        # 先校验当前选中的工作空间是不是一个有效的工作空间集合
        workspace_collection = bpy.context.collection
        result = CollectionUtils.is_valid_ssmt_workspace_collection_v2(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}
    
        # 调用对应游戏的生成Mod逻辑
        if GlobalConfig.logic_name == LogicName.WutheringWaves:
            migoto_mod_model = ModModelWWMI(workspace_collection=workspace_collection)
            migoto_mod_model.generate_unreal_vs_config_ini()

        elif GlobalConfig.logic_name == LogicName.YYSLS:
            migoto_mod_model = ModModelYYSLS(workspace_collection=workspace_collection)
            migoto_mod_model.generate_unity_vs_config_ini()

        elif GlobalConfig.logic_name == LogicName.CTXMC or GlobalConfig.logic_name == LogicName.IdentityV2 or GlobalConfig.logic_name == LogicName.NierR:
            migoto_mod_model = ModModelIdentityV(workspace_collection=workspace_collection)

            migoto_mod_model.generate_unity_vs_config_ini()
        elif GlobalConfig.logic_name == LogicName.GenshinImpact or GlobalConfig.logic_name == LogicName.HonkaiImpact3 or GlobalConfig.logic_name == LogicName.UnityVS or GlobalConfig.logic_name == LogicName.ZenlessZoneZero:
            migoto_mod_model = ModModelUnity(workspace_collection=workspace_collection)
            migoto_mod_model.generate_unity_vs_config_ini()

        elif GlobalConfig.logic_name == LogicName.HonkaiStarRail:
            migoto_mod_model = ModModelHonkaiStarRail(workspace_collection=workspace_collection)
            migoto_mod_model.generate_unity_cs_config_ini()

        elif GlobalConfig.logic_name == LogicName.AILIMIT or GlobalConfig.logic_name == LogicName.UnityCS:
            migoto_mod_model = ModModelUnity(workspace_collection=workspace_collection)
            migoto_mod_model.generate_unity_cs_config_ini()

        elif GlobalConfig.logic_name == LogicName.UnityCPU:
            migoto_mod_model = ModModelUnity(workspace_collection=workspace_collection)
            migoto_mod_model.generate_unity_vs_config_ini()

        else:
            self.report({'ERROR'},"当前逻辑暂不支持生成Mod")
            return {'FINISHED'}
        

        self.report({'INFO'},TR.translate("Generate Mod Success!"))
        TimerUtils.End("GenerateMod Mod")

        CommandUtils.OpenGeneratedModFolder()
        return {'FINISHED'}