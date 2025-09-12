import bpy

from ..utils.timer_utils import TimerUtils
from ..utils.translate_utils import TR
from ..utils.command_utils import CommandUtils
from ..utils.collection_utils import CollectionUtils

from ..config.main_config import GlobalConfig, LogicName
from ..common.branch_model import M_GlobalKeyCounter


from ..games.Unity import ModModelUnity
from ..games.HonkaiStarRail import ModModelHonkaiStarRail
from ..games.IdentityV import ModModelIdentityV
from ..games.YYSLS import ModModelYYSLS
from ..games.WWMI import ModModelWWMI
from ..games.SnowBreak import ModModelSnowBreak

class PanelGenerateModConfig(bpy.types.Panel):
    bl_label = "生成Mod配置"
    bl_idname = "VIEW3D_PT_CATTER_GenerateMod_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TheHerta'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # 根据当前游戏类型判断哪些应该显示哪些不显示。
        # 因为UnrealVS显然无法支持这里所有的特性，每个游戏只能支持一部分特性。

        # 任何游戏都能贴图标记
        if GlobalConfig.logic_name == LogicName.WutheringWaves:
            layout.prop(context.scene.properties_generate_mod, "only_use_marked_texture",text="只使用标记过的贴图")
            layout.prop(context.scene.properties_wwmi, "ignore_muted_shape_keys")
            layout.prop(context.scene.properties_wwmi, "apply_all_modifiers")

        layout.prop(context.scene.properties_generate_mod, "forbid_auto_texture_ini",text="禁止自动贴图流程")

        if GlobalConfig.logic_name != LogicName.UnityCPU:
            layout.prop(context.scene.properties_generate_mod, "recalculate_tangent",text="向量归一化法线存入TANGENT(全局)")

        if GlobalConfig.logic_name == LogicName.HonkaiImpact3:
            layout.prop(context.scene.properties_generate_mod, "recalculate_color",text="算术平均归一化法线存入COLOR(全局)")

        layout.prop(context.scene.properties_generate_mod, "position_override_filter_draw_type",text="Position替换添加DRAW_TYPE=1判断")
        layout.prop(context.scene.properties_generate_mod, "vertex_limit_raise_add_filter_index",text="VertexLimitRaise添加filter_index过滤器")
        layout.prop(context.scene.properties_generate_mod, "slot_style_texture_add_filter_index",text="槽位风格贴图添加filter_index过滤器")

        # 绝区零特有的SlotFix技术
        if GlobalConfig.logic_name == LogicName.ZenlessZoneZero:
            layout.prop(context.scene.properties_generate_mod, "zzz_use_slot_fix")
        
        # 所有的游戏都要能支持生成分支架构面板Mod
        layout.prop(context.scene.properties_generate_mod, "generate_branch_mod_gui",text="生成分支架构Mod面板(测试中)")

        # 默认习惯肯定是要显示这个的，但是由于不经常点击关闭，所以放在最后面
        layout.prop(context.scene.properties_generate_mod, "open_mod_folder_after_generate_mod",text="生成Mod后打开Mod所在文件夹")
        

class SSMTGenerateMod(bpy.types.Operator):
    bl_idname = "ssmt.generate_mod"
    bl_label = TR.translate("生成Mod")
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。使用前确保取消隐藏所有要导出的模型以及集合"

    def execute(self, context):
        TimerUtils.Start("GenerateMod Mod")

        M_GlobalKeyCounter.initialize()

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
        elif GlobalConfig.logic_name == LogicName.SnowBreak:
            migoto_mod_model = ModModelSnowBreak(workspace_collection=workspace_collection)
            migoto_mod_model.generate_ini()
        else:
            self.report({'ERROR'},"当前逻辑暂不支持生成Mod")
            return {'FINISHED'}
        

        self.report({'INFO'},TR.translate("Generate Mod Success!"))
        TimerUtils.End("GenerateMod Mod")

        CommandUtils.OpenGeneratedModFolder()
        return {'FINISHED'}