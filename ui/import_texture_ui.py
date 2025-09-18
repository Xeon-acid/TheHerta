import bpy
import os
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList
from bpy_extras.io_utils import ImportHelper
import bpy.utils.previews

from ..config.main_config import GlobalConfig

# 存储预览图集合
preview_collections = {}

# 定义图片列表项
class SSMT_ImportTexture_ImageListItem(PropertyGroup):
    name: StringProperty(name="Image Name") # type: ignore
    filepath: StringProperty(name="File Path") # type: ignore

# 自定义UI列表显示图片和缩略图
class SSMT_ImportTexture_IMAGE_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        pcoll = preview_collections["main"]
        
        if self.layout_type in {'DEFAULT', 'Expand'}:
            # 尝试获取预览图标
            if item.name in pcoll:
                layout.template_icon(icon_value=pcoll[item.name].icon_id, scale=1.0)
            else:
                layout.label(text="", icon='IMAGE_DATA')
            
            layout.label(text=item.name)
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            if item.name in pcoll:
                layout.template_icon(icon_value=pcoll[item.name].icon_id, scale=6.0)
            else:
                layout.label(text="", icon='IMAGE_DATA')

# 选择文件夹操作符
class SSMT_ImportTexture_WM_OT_SelectImageFolder(Operator, ImportHelper):
    bl_idname = "wm.select_image_folder"
    bl_label = "Select Folder with Images"
    
    directory: StringProperty(subtype='DIR_PATH') # type: ignore
    filter_folder: BoolProperty(default=True, options={'HIDDEN'}) # type: ignore
    filter_image: BoolProperty(default=False, options={'HIDDEN'}) # type: ignore

    def execute(self, context):
        # 清空之前的列表
        context.scene.image_list.clear()
        
        # 清空预览集合
        pcoll = preview_collections["main"]
        pcoll.clear()
        
        # 支持的图片格式
        image_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.tga', '.exr', '.hdr')
        
        # 遍历文件夹，收集图片文件
        image_count = 0
        for filename in os.listdir(self.directory):
            if filename.lower().endswith(image_extensions):
                full_path = os.path.join(self.directory, filename)
                if os.path.isfile(full_path):
                    item = context.scene.image_list.add()
                    item.name = filename
                    item.filepath = full_path
                    
                    # 加载预览图
                    try:
                        thumb = pcoll.load(filename, full_path, 'IMAGE')
                        image_count += 1
                    except Exception as e:
                        print(f"Could not load preview for {filename}: {e}")
        
        self.report({'INFO'}, f"Scanned {image_count} images.")
        return {'FINISHED'}

# 自动检测并设置DedupedTextures_jpg文件夹
class SSMT_ImportTexture_WM_OT_AutoDetectTextureFolder(Operator):
    bl_idname = "wm.auto_detect_texture_folder"
    bl_label = "Auto Detect Texture Folder"
    
    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}
        
        # 获取第一个选中的对象
        obj = selected_objects[0]
        obj_name = obj.name
        
        # 构建路径
        selected_drawib_folder_path = os.path.join(GlobalConfig.path_workspace_folder(),  obj_name.split("-")[0] + "\\"  )
        
        deduped_textures_jpg_folder_path = os.path.join(
            selected_drawib_folder_path, 
            "DedupedTextures_jpg\\"
        )
        
        # 检查路径是否存在
        if not os.path.exists(deduped_textures_jpg_folder_path):
            self.report({'ERROR'}, f"DedupedTextures_jpg folder not found at: {deduped_textures_jpg_folder_path}")
            return {'CANCELLED'}
        
        # 清空之前的列表和预览
        context.scene.image_list.clear()
        pcoll = preview_collections["main"]
        pcoll.clear()
        
        # 支持的图片格式
        image_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.tga', '.exr', '.hdr')
        
        # 遍历文件夹，收集图片文件
        image_count = 0
        for filename in os.listdir(deduped_textures_jpg_folder_path):
            if filename.lower().endswith(image_extensions):
                full_path = os.path.join(deduped_textures_jpg_folder_path, filename)
                if os.path.isfile(full_path):
                    item = context.scene.image_list.add()
                    item.name = filename
                    item.filepath = full_path
                    
                    # 加载预览图
                    try:
                        thumb = pcoll.load(filename, full_path, 'IMAGE')
                        image_count += 1
                    except Exception as e:
                        print(f"Could not load preview for {filename}: {e}")
        
        self.report({'INFO'}, f"Auto-detected and loaded {image_count} images from DedupedTextures_jpg folder.")
        return {'FINISHED'}

# 刷新预览操作符（可选，用于调试）
class SSMT_ImportTexture_WM_OT_RefreshPreviews(Operator):
    bl_idname = "wm.refresh_previews"
    bl_label = "Refresh Previews"
    
    def execute(self, context):
        pcoll = preview_collections["main"]
        pcoll.clear()
        
        for item in context.scene.image_list:
            try:
                pcoll.load(item.name, item.filepath, 'IMAGE')
            except Exception as e:
                print(f"Could not load preview for {item.name}: {e}")
        
        self.report({'INFO'}, "Previews refreshed.")
        return {'FINISHED'}

# 应用图片到材质操作符
class SSMT_ImportTexture_WM_OT_ApplyImageToMaterial(Operator):
    bl_idname = "wm.apply_image_to_material"
    bl_label = "Apply Image to Selected Objects"
    
    def execute(self, context):
        scene = context.scene
        selected_index = scene.image_list_index
        
        if selected_index < 0 or selected_index >= len(scene.image_list):
            self.report({'ERROR'}, "No image selected in the list.")
            return {'CANCELLED'}
        
        selected_image = scene.image_list[selected_index]
        image_path = selected_image.filepath
        
        # 获取或创建图像数据块
        image_data = bpy.data.images.load(image_path, check_existing=True)
        
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}
        
        applied_count = 0
        for obj in selected_objects:
            if obj.type != 'MESH':
                continue  # 跳过非网格对象
            
            # 确保对象有材质数据块
            if not obj.data.materials:
                mat = bpy.data.materials.new(name=f"Mat_{selected_image.name}")
                obj.data.materials.append(mat)
            else:
                # 使用第一个材质槽
                mat = obj.data.materials[0]
            
            # 确保材质使用节点
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            
            # 查找或创建Principled BSDF节点
            bsdf_node = nodes.get("Principled BSDF")
            if not bsdf_node:
                bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
                bsdf_node.location = (0, 0)
                
                # 获取材质输出节点
                output_node = nodes.get("Material Output")
                if not output_node:
                    output_node = nodes.new(type='ShaderNodeOutputMaterial')
                    output_node.location = (400, 0)
                
                # 连接到输出
                links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
            
            # 创建图像纹理节点
            tex_image = nodes.new('ShaderNodeTexImage')
            tex_image.image = image_data
            tex_image.location = (-300, 0)
            
            # 将图像纹理节点的Color输出连接到BSDF的Base Color输入
            links.new(tex_image.outputs['Color'], bsdf_node.inputs['Base Color'])
            
            applied_count += 1
        
        self.report({'INFO'}, f"Applied {selected_image.name} to {applied_count} object(s).")
        return {'FINISHED'}

# 面板UI布局
class SSMT_ImportTexture_VIEW3D_PT_ImageMaterialPanel(Panel):
    bl_label = "快速贴图预览"
    bl_idname = "VIEW3D_PT_image_material_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TheHerta'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 自动检测按钮
        row = layout.row()
        row.operator("wm.auto_detect_texture_folder", icon='FILE_REFRESH', text="Auto Detect Texture Folder")
        
        # 文件夹选择按钮
        row = layout.row()
        row.operator("wm.select_image_folder", icon='FILE_FOLDER', text="Select Image Folder")
        
        # 显示图片数量信息
        if scene.image_list:
            layout.label(text=f"Found {len(scene.image_list)} images")
        
        # 显示图片列表
        if scene.image_list:
            row = layout.row()
            row.template_list(
                "SSMT_ImportTexture_IMAGE_UL_List",  # 修正为正确的类名
                "Image List", 
                scene, 
                "image_list", 
                scene, 
                "image_list_index",
                rows=6
            )
        else:
            layout.label(text="No images found. Select a folder first.")
        
        # 应用材质按钮
        row = layout.row()
        row.operator("wm.apply_image_to_material", icon='MATERIAL_DATA')
        
        # 显示当前选中图片的预览
        if scene.image_list and scene.image_list_index >= 0 and scene.image_list_index < len(scene.image_list):
            selected_item = scene.image_list[scene.image_list_index]
            pcoll = preview_collections["main"]
            
            if selected_item.name in pcoll:
                box = layout.box()
                box.label(text="Preview:")
                box.template_icon(icon_value=pcoll[selected_item.name].icon_id, scale=10.0)