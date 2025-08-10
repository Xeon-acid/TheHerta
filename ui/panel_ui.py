import bpy
import blf

import os

from bpy.types import SpaceView3D

from ..utils.migoto_utils import *
from ..config.main_config import * 
from .generate_mod_ui import *

from ..properties.properties_dbmt_path import Properties_DBMT_Path
from ..migoto.mesh_import_utils import MeshImportUtils
from ..migoto.migoto_binary_file import MigotoBinaryFile


from bpy_extras.io_utils import ImportHelper # 用于解决 AttributeError: 'IMPORT_MESH_OT_migoto_raw_buffers_mmt' object has no attribute 'filepath'

from .. import addon_updater_ops

# 用于选择DBMT所在文件夹，主要是这里能自定义逻辑从而实现保存DBMT路径，这样下次打开就还能读取到。
class OBJECT_OT_select_dbmt_folder(bpy.types.Operator):
    bl_idname = "object.select_dbmt_folder"
    bl_label = "选择SSMT-Package路径"

    directory: bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'HIDDEN'},
    ) # type: ignore

    def execute(self, context):
        scene = context.scene
        if self.directory:
            scene.dbmt_path.path = self.directory
            # print(f"Selected folder: {self.directory}")
            # 在这里放置你想要执行的逻辑
            # 比如验证路径是否有效、初始化某些资源等
            GlobalConfig.save_dbmt_path()
            
            self.report({'INFO'}, f"Folder selected: {self.directory}")
        else:
            self.report({'WARNING'}, "No folder selected.")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    

class Import3DMigotoRaw(bpy.types.Operator, ImportHelper):
    """Import raw 3DMigoto vertex and index buffers"""
    bl_idname = "import_mesh.migoto_raw_buffers_mmt"
    bl_label = "导入.fmt .ib .vb格式模型"
    bl_description = "导入3Dmigoto格式的 .ib .vb .fmt文件，只需选择.fmt文件即可"

    # 我们只需要选择fmt文件即可，因为其它文件都是根据fmt文件的前缀来确定的。
    # 所以可以实现一个.ib 和 .vb文件存在多个数据类型描述的.fmt文件的导入。
    filename_ext = '.fmt'

    filter_glob: bpy.props.StringProperty(
        default='*.fmt',
        options={'HIDDEN'},
    ) # type: ignore

    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    ) # type: ignore

    def execute(self, context):
        # 我们需要添加到一个新建的集合里，方便后续操作
        # 这里集合的名称需要为当前文件夹的名称
        dirname = os.path.dirname(self.filepath)

        collection_name = os.path.basename(dirname)
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)

        # 如果用户不选择任何fmt文件，则默认返回读取所有的fmt文件。
        import_filename_list = []
        if len(self.files) == 1:
            if str(self.filepath).endswith(".fmt"):
                import_filename_list.append(self.filepath)
            else:
                for filename in os.listdir(self.filepath):
                    if filename.endswith(".fmt"):
                        import_filename_list.append(filename)
        else:
            for fmtfile in self.files:
                import_filename_list.append(fmtfile.name)

        # 逐个fmt文件导入
        for fmt_file_name in import_filename_list:
            fmt_file_path = os.path.join(dirname, fmt_file_name)
            mbf = MigotoBinaryFile(fmt_path=fmt_file_path)
            obj_result = MeshImportUtils.create_mesh_obj_from_mbf(mbf=mbf)
            collection.objects.link(obj_result)
        
        # Select all objects under collection (因为用户习惯了导入后就是全部选中的状态). 
        CollectionUtils.select_collection_objects(collection)

        return {'FINISHED'}


# 3Dmigoto属性绘制
def draw_migoto_overlay():
    """在 3D 视图左下角绘制自定义信息"""
    context = bpy.context  # 直接使用 bpy.context 获取完整上下文
    if len(context.selected_objects) == 0:
        return

    obj = context.selected_objects[0]
    region = context.region
    font_id = 0  # 默认字体

    # 设置绘制位置（左上角，稍微偏移避免遮挡默认信息）
    x = 70
    y = 60  # 从顶部往下偏移

    # 获取自定义属性
    gametypename = obj.get("3DMigoto:GameTypeName", None)
    recalculate_tangent = obj.get("3DMigoto:RecalculateTANGENT", None)
    recalculate_color = obj.get("3DMigoto:RecalculateCOLOR", None)

    # 设置字体样式（可选）
    blf.size(font_id, 24)  # 12pt 大小
    blf.color(font_id, 1, 1, 1, 1)  # 白色

    # 绘制文本
    if gametypename:
        y += 20
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, f"GameType: {gametypename}")

        y += 20
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, f"Recalculate TANGENT: {recalculate_tangent}")
        

        y += 20
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, f"Recalculate COLOR: {recalculate_color}")

# 存储 draw_handler 引用，方便后续移除
migoto_draw_handler = None





class PanelModelImportConfig(bpy.types.Panel):
    bl_label = "导入模型配置"
    bl_idname = "VIEW3D_PT_CATTER_WorkSpace_IO_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TheHerta'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.properties_import_model,"model_scale",text="模型导入大小比例")
        
        if GlobalConfig.logic_name == LogicName.WutheringWaves:
            layout.prop(context.scene.properties_wwmi,"import_merged_vgmap",text="使用融合统一顶点组")


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
        
    

class PanelButtons(bpy.types.Panel):
    bl_label = "SSMT基础面板" 
    bl_idname = "VIEW3D_PT_CATTER_Buttons_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TheHerta'
    

    def draw(self, context):
        layout = self.layout

        # use_sepecified_dbmt
        layout.prop(context.scene.dbmt_path, "use_specified_dbmt",text="使用指定位置的SSMT-Package")

        if Properties_DBMT_Path.use_specified_dbmt():
            # Path button to choose DBMT-GUI.exe location folder.
            row = layout.row()
            row.operator("object.select_dbmt_folder")

            ssmt_package_3dmigoto_path = os.path.join(Properties_DBMT_Path.path(), "3Dmigoto-GameMod-Fork")
            if not os.path.exists(ssmt_package_3dmigoto_path):
                layout.label(text="Error:Please select SSMT-Package path ", icon='ERROR')

        
        GlobalConfig.read_from_main_json()

        layout.label(text="SSMT-Package路径: " + GlobalConfig.dbmtlocation)
        # print(MainConfig.dbmtlocation)

        layout.label(text="当前游戏: " + GlobalConfig.gamename)
        layout.label(text="当前逻辑: " + GlobalConfig.logic_name)
        layout.label(text="当前工作空间: " + GlobalConfig.workspacename)

        layout.prop(context.scene.properties_import_model,"use_mirror_workflow",text="使用非镜像工作流")
        
        # 导入 ib vb fmt格式文件
        layout.operator("import_mesh.migoto_raw_buffers_mmt",icon='IMPORT')


        # 目前只有WuWa、WWMI使用旧的集合架构
        # TODO 后续需要全部迁移到新的集合架构
        if GlobalConfig.logic_name == LogicName.WutheringWaves:
            layout.operator("ssmt.import_all_from_workspace_v2",icon='IMPORT')
        
        layout.operator("ssmt.import_all_from_workspace_v3",icon='IMPORT')

        if GlobalConfig.logic_name == LogicName.HonkaiStarRail:
            layout.operator("ssmt.generate_mod_hsr_v3",icon='EXPORT')
        elif GlobalConfig.logic_name == LogicName.AILIMIT:
            layout.operator("ssmt.generate_mod_hsr_v3",icon='EXPORT')
        elif GlobalConfig.logic_name == LogicName.YYSLS:
            layout.operator("ssmt.generate_mod_yysls_v2")
        elif GlobalConfig.logic_name == LogicName.CTXMC:
            layout.operator("ssmt.generate_mod_ctx_mc")
        elif GlobalConfig.logic_name == LogicName.WutheringWaves:
            layout.operator("herta.export_mod_wwmi",text="生成Mod(旧)",icon='EXPORT')
            layout.operator("ssmt.generate_mod_wwmi_v3")
        elif GlobalConfig.logic_name == LogicName.GenshinImpact:
            layout.operator("ssmt.generate_mod_unity_vs_v2")
        elif GlobalConfig.logic_name == LogicName.HonkaiImpact3:
            layout.operator("ssmt.generate_mod_unity_vs_v2")
        else:
            if GlobalConfig.logic_name == LogicName.UnityVS:
                layout.operator("ssmt.generate_mod_unity_vs_v2")
            elif GlobalConfig.logic_name == LogicName.UnityCS:
                layout.operator("ssmt.generate_mod_unity_cs_v2")
            elif GlobalConfig.logic_name == LogicName.ZenlessZoneZero:
                layout.operator("ssmt.generate_mod_unity_vs_v2")
            else:
                layout.label(text= "Generate Mod for " + GlobalConfig.gamename + " Not Supported Yet.")

