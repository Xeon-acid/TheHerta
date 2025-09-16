import bpy
import math

from ..common.migoto_format import M_Key, M_DrawIndexed, M_Condition,D3D11GameType,TextureReplace
from ..config.import_config import GlobalConfig
from ..common.draw_ib_model import DrawIBModel

from ..common.branch_model import BranchModel,M_GlobalKeyCounter
from ..common.m_ini_builder import M_IniBuilder,M_IniSection,M_SectionType
from ..config.properties_generate_mod import Properties_GenerateMod
from ..common.m_ini_helper import M_IniHelperV2,M_IniHelperV3

from ..common.m_ini_helper_gui import M_IniHelperGUI

class ModModelHonkaiStarRail:
    def __init__(self,workspace_collection:bpy.types.Collection):
        # (1) 统计全局分支模型
        self.branch_model = BranchModel(workspace_collection=workspace_collection)

        # (2) 抽象每个DrawIB为DrawIBModel
        self.drawib_drawibmodel_dict:dict[str,DrawIBModel] = {}
        self.parse_draw_ib_draw_ib_model_dict()

        # (3) 这些属性用于ini生成
        self.vlr_filter_index_indent = ""
        self.texture_hash_filter_index_dict = {}

    def parse_draw_ib_draw_ib_model_dict(self):
        '''
        根据obj的命名规则，推导出DrawIB并抽象为DrawIBModel
        如果用户用不到某个DrawIB的话，就可以隐藏掉对应的obj
        隐藏掉的obj就不会被统计生成DrawIBModel，做到只导入模型，不生成Mod的效果。
        '''
        for draw_ib in self.branch_model.draw_ib__component_count_list__dict.keys():
            draw_ib_model = DrawIBModel(draw_ib=draw_ib,branch_model=self.branch_model)
            self.drawib_drawibmodel_dict[draw_ib] = draw_ib_model


    
    def add_vertex_limit_raise_section(self,config_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        '''
        VertexLimitRaise部分，用于突破顶点数限制
        '''
        d3d11GameType = draw_ib_model.d3d11GameType
        draw_ib = draw_ib_model.draw_ib

        if d3d11GameType.GPU_PreSkinning:
            vertexlimit_section = M_IniSection(M_SectionType.TextureOverrideVertexLimitRaise)

            vertexlimit_section.append("[TextureOverride_" + draw_ib + "_" + draw_ib_model.draw_ib_alias + "_Draw" + "]")
            vertexlimit_section.append("hash = " + draw_ib_model.import_config.vertex_limit_hash)

            if draw_ib_model.draw_number > draw_ib_model.import_config.original_vertex_count:
                vertexlimit_section.append("override_byte_stride = " + str(d3d11GameType.CategoryStrideDict["Position"]))
                vertexlimit_section.append("override_vertex_count = " + str(draw_ib_model.draw_number))
                # 这里步长为4，是因为override_byte_stride * override_vertex_count 后要除以 4来得到 uav的num_elements
                vertexlimit_section.append("uav_byte_stride = 4")
                vertexlimit_section.new_line()

            config_ini_builder.append_section(vertexlimit_section)

    
    def add_resource_texture_sections(self,ini_builder,draw_ib_model:DrawIBModel):
        '''
        Add texture resource.
        只有槽位风格贴图会用到，因为Hash风格贴图有专门的方法去声明这个。
        '''
        if Properties_GenerateMod.forbid_auto_texture_ini():
            return 
        
        resource_texture_section = M_IniSection(M_SectionType.ResourceTexture)
        for resource_name, texture_filename in draw_ib_model.import_config.TextureResource_Name_FileName_Dict.items():
            if "_Slot_" in texture_filename:
                resource_texture_section.append("[" + resource_name + "]")
                resource_texture_section.append("filename = Texture/" + texture_filename)
                resource_texture_section.new_line()

        ini_builder.append_section(resource_texture_section)


    def add_texture_override_vb_sections(self,config_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        # 声明TextureOverrideVB部分，只有使用GPU-PreSkinning时是直接替换hash对应槽位
        d3d11GameType = draw_ib_model.d3d11GameType
        draw_ib = draw_ib_model.draw_ib

        if d3d11GameType.GPU_PreSkinning:
            texture_override_vb_section = M_IniSection(M_SectionType.TextureOverrideVB)
            texture_override_vb_section.append("; " + draw_ib + " ----------------------------")
            for category_name in d3d11GameType.OrderedCategoryNameList:
                category_hash = draw_ib_model.import_config.category_hash_dict[category_name]
                category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]

                texture_override_vb_namesuffix = "VB_" + draw_ib + "_" + draw_ib_model.draw_ib_alias + "_" + category_name

                if category_name != "Position":
                    texture_override_vb_section.append("[TextureOverride_" + texture_override_vb_namesuffix + "]")
                    texture_override_vb_section.append("hash = " + category_hash)

                    if category_name != "Texcoord":
                        texture_override_vb_section.append("handling = skip")

                # 如果出现了VertexLimitRaise，Texcoord槽位需要检测filter_index才能替换
                filterindex_indent_prefix = ""
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                    if self.vlr_filter_index_indent != "":
                        texture_override_vb_section.append("if vb0 == " + str(3000 + M_GlobalKeyCounter.generated_mod_number))

                # 遍历获取所有在当前分类hash下进行替换的分类，并添加对应的资源替换
                for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                    position_category_slot = d3d11GameType.CategoryExtractSlotDict["Position"]
                    blend_category_slot = d3d11GameType.CategoryExtractSlotDict["Blend"]
                     
                    if category_name == draw_category_name:
                        if original_category_name == "Position":
                            pass
                        elif original_category_name == "Blend":
                            texture_override_vb_section.append("vb2 = Resource" + draw_ib + "Blend")
                            texture_override_vb_section.append("if DRAW_TYPE == 1")
                            texture_override_vb_section.append("  vb0 = Resource" + draw_ib + "Position")
                            texture_override_vb_section.append("draw = " + str(draw_ib_model.draw_number) + ", 0")
                            texture_override_vb_section.append("endif")
                            texture_override_vb_section.append("if DRAW_TYPE == 8")
                            texture_override_vb_section.append("  Resource\\SRMI\\PositionBuffer = ref Resource" + draw_ib + "PositionCS" )
                            texture_override_vb_section.append("  Resource\\SRMI\\BlendBuffer = ref Resource" + draw_ib + "BlendCS" )
                            texture_override_vb_section.append("  $\\SRMI\\vertex_count = " + str(draw_ib_model.draw_number))
                            texture_override_vb_section.append("endif")
                            
                        else:
                            category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                            texture_override_vb_section.append(filterindex_indent_prefix  + category_original_slot + " = Resource" + draw_ib + original_category_name)

                # 对应if vb0 == 3000的结束
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                    if self.vlr_filter_index_indent != "":
                        texture_override_vb_section.append("endif")
                
                # 分支架构，如果是Position则需提供激活变量
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                    if len(self.branch_model.keyname_mkey_dict.keys()) != 0:
                        texture_override_vb_section.append("$active" + str(M_GlobalKeyCounter.generated_mod_number) + " = 1")

                        if Properties_GenerateMod.generate_branch_mod_gui():
                            texture_override_vb_section.append("$ActiveCharacter = 1")

                texture_override_vb_section.new_line()
            config_ini_builder.append_section(texture_override_vb_section)
            
            
    def add_texture_override_ib_sections(self,config_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        texture_override_ib_section = M_IniSection(M_SectionType.TextureOverrideIB)
        draw_ib = draw_ib_model.draw_ib
        d3d11GameType = draw_ib_model.d3d11GameType

        # texture_override_ib_section.append("[TextureOverride_IB_" + draw_ib + "_" + draw_ib_model.draw_ib_alias + "]")
        # texture_override_ib_section.append("hash = " + draw_ib)
        # texture_override_ib_section.append("handling = skip")
        # texture_override_ib_section.new_line()

        # texture_override_ib_section.append("drawindexed = auto")

        for count_i in range(len(draw_ib_model.import_config.part_name_list)):
            match_first_index = draw_ib_model.import_config.match_first_index_list[count_i]
            part_name = draw_ib_model.import_config.part_name_list[count_i]

            style_part_name = "Component" + part_name
            ib_resource_name = "Resource_" + draw_ib+ "_" + style_part_name

            texture_override_ib_namesuffix = "IB_" + draw_ib  + "_" + draw_ib_model.draw_ib_alias  + "_" + style_part_name
            texture_override_ib_section.append("[TextureOverride_" + texture_override_ib_namesuffix + "]")
            texture_override_ib_section.append("hash = " + draw_ib)
            texture_override_ib_section.append("match_first_index = " + match_first_index)
            texture_override_ib_section.append("handling = skip")

            if self.vlr_filter_index_indent != "":
                texture_override_ib_section.append("if vb0 == " + str(3000 + M_GlobalKeyCounter.generated_mod_number))

            # texture_override_ib_section.append(self.vlr_filter_index_indent + "handling = skip")


            # If ib buf is emprt, continue to avoid add ib resource replace.
            ib_buf = draw_ib_model.componentname_ibbuf_dict.get("Component " + part_name,None)
            if ib_buf is None or len(ib_buf) == 0:
                texture_override_ib_section.new_line()
                continue

            # Add ib replace
            texture_override_ib_section.append(self.vlr_filter_index_indent + "ib = " + ib_resource_name)

            # Add slot style texture slot replace.
            if not Properties_GenerateMod.forbid_auto_texture_ini():
                slot_texturereplace_dict = draw_ib_model.import_config.PartName_SlotTextureReplaceDict_Dict.get(part_name,None)
                # It may not have auto texture
                if slot_texturereplace_dict is not None:
                    for slot,texture_replace_obj in slot_texturereplace_dict.items():
                        if texture_replace_obj.style == "Slot":
                            texture_override_ib_section.append(self.vlr_filter_index_indent + slot + " = " + texture_replace_obj.resource_name)

            # 如果不使用GPU-Skinning即为Object类型，此时需要在ib下面替换对应槽位
            if not d3d11GameType.GPU_PreSkinning:
                for category_name in d3d11GameType.OrderedCategoryNameList:
                    category_hash = draw_ib_model.import_config.category_hash_dict[category_name]
                    category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]

                    for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                        if original_category_name == draw_category_name:
                            category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                            texture_override_ib_section.append(self.vlr_filter_index_indent + category_original_slot + " = Resource" + draw_ib + original_category_name)
            

            # Component DrawIndexed输出
            component_name = "Component " + part_name 

            component_model = draw_ib_model.component_name_component_model_dict[component_name]
            drawindexed_str_list = M_IniHelperV2.get_drawindexed_str_list(component_model.final_ordered_draw_obj_model_list)
            for drawindexed_str in drawindexed_str_list:
                texture_override_ib_section.append(drawindexed_str)
            
            if self.vlr_filter_index_indent != "":
                texture_override_ib_section.append("endif")
                texture_override_ib_section.new_line()


        config_ini_builder.append_section(texture_override_ib_section)

    def add_unity_cs_resource_vb_sections(self,config_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        '''
        Add Resource VB Section (HSR3.2)
        '''
        resource_vb_section = M_IniSection(M_SectionType.ResourceBuffer)

        # 先加入普通的Buffer
        for category_name in draw_ib_model.d3d11GameType.OrderedCategoryNameList:
            resource_vb_section.append("[Resource" + draw_ib_model.draw_ib + category_name + "]")
            resource_vb_section.append("type = Buffer")
            resource_vb_section.append("stride = " + str(draw_ib_model.d3d11GameType.CategoryStrideDict[category_name]))
            resource_vb_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + category_name + ".buf")
            # resource_vb_section.append(";VertexCount: " + str(draw_ib_model.draw_number))
            resource_vb_section.new_line()
        
        # 再加入CS的Buffer，主要是Position和Blend
        for category_name in draw_ib_model.d3d11GameType.OrderedCategoryNameList:
            if category_name == "Position" or category_name == "Blend":
                resource_vb_section.append("[Resource" + draw_ib_model.draw_ib + category_name + "CS]")
                resource_vb_section.append("type = StructuredBuffer")
                resource_vb_section.append("stride = " + str(draw_ib_model.d3d11GameType.CategoryStrideDict[category_name]))
                resource_vb_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + category_name + ".buf")
                # resource_vb_section.append(";VertexCount: " + str(draw_ib_model.draw_number))
                resource_vb_section.new_line()

        '''
        Add Resource IB Section

        We default use R32_UINT because R16_UINT have a very small number limit.
        '''
        for count_i in range(len(draw_ib_model.import_config.part_name_list)):
            partname = draw_ib_model.import_config.part_name_list[count_i]
            style_partname = "Component" + partname
            ib_resource_name = "Resource_" + draw_ib_model.draw_ib + "_" + style_partname

            
            resource_vb_section.append("[" + ib_resource_name + "]")
            resource_vb_section.append("type = Buffer")
            resource_vb_section.append("format = DXGI_FORMAT_R32_UINT")
            resource_vb_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + style_partname + ".buf")
            resource_vb_section.new_line()
        
        config_ini_builder.append_section(resource_vb_section)
    


    def add_texture_filter_index(self,ini_builder:M_IniBuilder):
        if not Properties_GenerateMod.slot_style_texture_add_filter_index():
            return 

        filter_index_count = 0
        for draw_ib, draw_ib_model in self.drawib_drawibmodel_dict.items():
            for partname,slot_texture_replace_dict in draw_ib_model.import_config.PartName_SlotTextureReplaceDict_Dict.items():
                for slot, texture_replace in slot_texture_replace_dict.items():
                    if texture_replace.hash in self.texture_hash_filter_index_dict:
                        continue
                    else:
                        filter_index = 6000 + filter_index_count
                        filter_index_count = filter_index_count + 1
                        self.texture_hash_filter_index_dict[texture_replace.hash] = filter_index
        

        texture_filter_index_section = M_IniSection(M_SectionType.TextureOverrideTexture)
        for hash_value, filter_index in self.texture_hash_filter_index_dict.items():
            texture_filter_index_section.append("[TextureOverride_Texture_" + hash_value + "]")
            texture_filter_index_section.append("hash = " + hash_value)
            texture_filter_index_section.append("filter_index = " + str(filter_index))
            texture_filter_index_section.new_line()

        ini_builder.append_section(texture_filter_index_section)





    def generate_unity_cs_config_ini(self):
        '''
        test
        '''
        config_ini_builder = M_IniBuilder()

        M_IniHelperV2.generate_hash_style_texture_ini(ini_builder=config_ini_builder,drawib_drawibmodel_dict=self.drawib_drawibmodel_dict)


        if Properties_GenerateMod.slot_style_texture_add_filter_index():
            self.add_texture_filter_index(ini_builder= config_ini_builder)

        for draw_ib, draw_ib_model in self.drawib_drawibmodel_dict.items():

   
            # [TextureOverrideVertexLimitRaise]
            self.add_vertex_limit_raise_section(config_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model) 
            # [TextureOverrideVB]
            self.add_texture_override_vb_sections(config_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model) 
            # [TextureOverrideIB]
            self.add_texture_override_ib_sections(config_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model) 

            # Resource.ini
            self.add_unity_cs_resource_vb_sections(config_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
            self.add_resource_texture_sections(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)

            M_IniHelperV2.move_slot_style_textures(draw_ib_model=draw_ib_model)

            M_GlobalKeyCounter.generated_mod_number = M_GlobalKeyCounter.generated_mod_number + 1

        M_IniHelperV3.add_branch_key_sections(ini_builder=config_ini_builder,key_name_mkey_dict=self.branch_model.keyname_mkey_dict)

        M_IniHelperGUI.add_branch_mod_gui_section(ini_builder=config_ini_builder,key_name_mkey_dict=self.branch_model.keyname_mkey_dict)

        config_ini_builder.save_to_file(GlobalConfig.path_generate_mod_folder() + GlobalConfig.workspacename + ".ini")
        