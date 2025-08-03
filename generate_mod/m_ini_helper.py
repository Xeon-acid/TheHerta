import os
import shutil

from .m_ini_builder import *
from ..utils.json_utils import JsonUtils
from ..config.main_config import GlobalConfig,LogicName
from ..properties.properties_generate_mod import Properties_GenerateMod
from .drawib_model_universal import DrawIBModelUniversal
from .m_counter import M_Counter
from ..migoto.migoto_format import ObjModel, M_Key

class M_IniHelperV2:
    @classmethod
    def get_drawindexed_str_list(cls,ordered_draw_obj_model_list) -> list[str]:
        # 在输出之前，我们需要根据condition对obj_model进行分组
        condition_str_obj_model_list_dict:dict[str,list[ObjModel]] = {}
        for obj_model in ordered_draw_obj_model_list:

            obj_model_list = condition_str_obj_model_list_dict.get(obj_model.condition.condition_str,[])
            
            obj_model_list.append(obj_model)
            condition_str_obj_model_list_dict[obj_model.condition.condition_str] = obj_model_list
        
        print(condition_str_obj_model_list_dict)

        drawindexed_str_list:list[str] = []
        for condition_str, obj_model_list in condition_str_obj_model_list_dict.items():
            if condition_str != "":
                drawindexed_str_list.append("if " + condition_str)
                for obj_model in obj_model_list:
                    drawindexed_str_list.append("  ; [mesh:" + obj_model.obj_name + "] [vertex_count:" + str(obj_model.drawindexed_obj.UniqueVertexCount) + "]" )
                    drawindexed_str_list.append("  " + obj_model.drawindexed_obj.get_draw_str())
                drawindexed_str_list.append("endif")
            else:
                for obj_model in obj_model_list:
                    drawindexed_str_list.append("; [mesh:" + obj_model.obj_name + "] [vertex_count:" + str(obj_model.drawindexed_obj.UniqueVertexCount) + "]" )
                    drawindexed_str_list.append(obj_model.drawindexed_obj.get_draw_str())
            drawindexed_str_list.append("")

        return drawindexed_str_list

    @classmethod
    def generate_hash_style_texture_ini(cls,ini_builder:M_IniBuilder,drawib_drawibmodel_dict:dict[str,DrawIBModelUniversal]):
        '''
        Generate Hash style TextureReplace.ini
        '''
        if Properties_GenerateMod.forbid_auto_texture_ini():
            return
        

        # 先统计当前标记的具有Slot风格的Hash值，后续Render里搞图片的时候跳过这些
        slot_style_texture_hash_list = []
        for draw_ib_model in drawib_drawibmodel_dict.values():
            for texture_file_name in draw_ib_model.TextureResource_Name_FileName_Dict.values():
                if "_Slot_" in texture_file_name:
                    texture_hash = texture_file_name.split("_")[2]
                    slot_style_texture_hash_list.append(texture_hash)
                    
        repeat_hash_list = []
        # 遍历当前drawib的Render文件夹
        for draw_ib,draw_ib_model in drawib_drawibmodel_dict.items():
            render_texture_folder_path = GlobalConfig.path_workspace_folder() + draw_ib + "\\" + "RenderTextures\\"

            render_texture_files = os.listdir(render_texture_folder_path)

            # 添加标记的Hash风格贴图
            for texture_file_name in draw_ib_model.TextureResource_Name_FileName_Dict.values():
                if "_Hash_" in texture_file_name:
                    texture_hash = texture_file_name.split("_")[2]

                    if texture_hash in repeat_hash_list:
                        continue
                    repeat_hash_list.append(texture_hash)

                    original_texture_file_path = GlobalConfig.path_extract_gametype_folder(draw_ib=draw_ib,gametype_name=draw_ib_model.d3d11GameType.GameTypeName) + texture_file_name

                    # same hash usually won't exists in two folder.
                    if not os.path.exists(original_texture_file_path):
                        continue

                    
                    target_texture_file_path = GlobalConfig.path_generatemod_texture_folder(draw_ib=draw_ib) + texture_file_name
                    
                    resource_and_textureoverride_texture_section = M_IniSection(M_SectionType.ResourceAndTextureOverride_Texture)
                    resource_and_textureoverride_texture_section.append("[Resource_Texture_" + texture_hash + "]")
                    resource_and_textureoverride_texture_section.append("filename = Texture/" + texture_file_name)
                    resource_and_textureoverride_texture_section.new_line()

                    resource_and_textureoverride_texture_section.append("[TextureOverride_" + texture_hash + "]")
                    resource_and_textureoverride_texture_section.append("; " + texture_file_name)
                    resource_and_textureoverride_texture_section.append("hash = " + texture_hash)
                    resource_and_textureoverride_texture_section.append("match_priority = 0")
                    resource_and_textureoverride_texture_section.append("this = Resource_Texture_" + texture_hash)
                    resource_and_textureoverride_texture_section.new_line()

                    ini_builder.append_section(resource_and_textureoverride_texture_section)

                    # copy only if target not exists avoid overwrite texture manually replaced by mod author.
                    if not os.path.exists(target_texture_file_path):
                        shutil.copy2(original_texture_file_path,target_texture_file_path)

            # 现在除了WWMI外都不使用全局Hash贴图风格，而是上面的标记的Hash风格贴图
            if GlobalConfig.logic_name != LogicName.WutheringWaves:
                continue

            # 如果WWMI只使用标记过的贴图，则跳过RenderTextures的生成
            elif Properties_GenerateMod.only_use_marked_texture():
                continue

            # 添加RenderTextures里的的贴图
            for render_texture_name in render_texture_files:
                texture_hash = render_texture_name.split("_")[0]
                
                if "!U!" in texture_hash:
                    continue

                if texture_hash in slot_style_texture_hash_list:
                    continue

                if texture_hash in repeat_hash_list:
                    continue
                repeat_hash_list.append(texture_hash)

                original_texture_file_path = render_texture_folder_path + render_texture_name

                # same hash usually won't exists in two folder.
                if not os.path.exists(original_texture_file_path):
                    continue

                
                target_texture_file_path = GlobalConfig.path_generatemod_texture_folder(draw_ib=draw_ib) + render_texture_name
                
                resource_and_textureoverride_texture_section = M_IniSection(M_SectionType.ResourceAndTextureOverride_Texture)
                resource_and_textureoverride_texture_section.append("[Resource_Texture_" + texture_hash + "]")
                resource_and_textureoverride_texture_section.append("filename = Texture/" + render_texture_name)
                resource_and_textureoverride_texture_section.new_line()

                resource_and_textureoverride_texture_section.append("[TextureOverride_" + texture_hash + "]")
                resource_and_textureoverride_texture_section.append("; " + render_texture_name)
                resource_and_textureoverride_texture_section.append("hash = " + texture_hash)
                resource_and_textureoverride_texture_section.append("match_priority = 0")
                resource_and_textureoverride_texture_section.append("this = Resource_Texture_" + texture_hash)
                resource_and_textureoverride_texture_section.new_line()

                ini_builder.append_section(resource_and_textureoverride_texture_section)

                # copy only if target not exists avoid overwrite texture manually replaced by mod author.
                if not os.path.exists(target_texture_file_path):
                    shutil.copy2(original_texture_file_path,target_texture_file_path)

        # if len(repeat_hash_list) != 0:
        #     texture_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + MainConfig.workspacename + "_Texture.ini")

    @classmethod
    def move_slot_style_textures(cls,draw_ib_model:DrawIBModelUniversal):
        '''
        Move all textures from extracted game type folder to generate mod Texture folder.
        Only works in default slot style texture.
        '''
        if Properties_GenerateMod.forbid_auto_texture_ini():
            return
        
        for texture_filename in draw_ib_model.TextureResource_Name_FileName_Dict.values():
            # 只有槽位风格会移动到目标位置
            if "_Slot_" in texture_filename:
                target_path = GlobalConfig.path_generatemod_texture_folder(draw_ib=draw_ib_model.draw_ib) + texture_filename
                source_path = draw_ib_model.import_config.extract_gametype_folder_path + texture_filename
                
                # only overwrite when there is no texture file exists.
                if not os.path.exists(target_path):
                    shutil.copy2(source_path,target_path)

    @classmethod
    def add_switchkey_constants_section(cls,ini_builder,draw_ib_model:DrawIBModelUniversal):
        '''
        声明SwitchKey的Constants变量
        '''
        if len(draw_ib_model.key_name_mkey_dict.keys()) != 0:
            constants_section = M_IniSection(M_SectionType.Constants)
            constants_section.SectionName = "Constants"
            constants_section.append("global $active" + str(M_Counter.generated_mod_number))
            for mkey in draw_ib_model.key_name_mkey_dict.values():
                key_str = "global persist " + mkey.key_name + " = " + str(mkey.initialize_value)
                constants_section.append(key_str) 

            ini_builder.append_section(constants_section)

    @classmethod
    def add_switchkey_present_section(cls,ini_builder,draw_ib_model:DrawIBModelUniversal):
        '''
        声明$active激活变量
        '''
        if len(draw_ib_model.key_name_mkey_dict.keys()) != 0:
            present_section = M_IniSection(M_SectionType.Present)
            present_section.SectionName = "Present"
            present_section.append("post $active" + str(M_Counter.generated_mod_number) + " = 0")
            ini_builder.append_section(present_section)
    
    @classmethod
    def add_switchkey_sections(cls,ini_builder:M_IniBuilder,draw_ib_model:DrawIBModelUniversal):
        '''
        声明按键切换和按键开关的变量 Key Section
        '''
        key_number = 0
        if len(draw_ib_model.key_name_mkey_dict.keys()) != 0:

            for mkey in draw_ib_model.key_name_mkey_dict.values():
                key_section = M_IniSection(M_SectionType.Key)
                key_section.append("[KeySwap_" + str(M_Counter.generated_mod_number) + "_" + str(key_number) + "]")
                if draw_ib_model.d3d11GameType.GPU_PreSkinning:
                    key_section.append("condition = $active" + str(M_Counter.generated_mod_number) + " == 1")
                key_section.append("key = " + mkey.key_value)
                key_section.append("type = cycle")

                key_value_number = len(mkey.value_list)
                key_cycle_str = ""
                for i in range(key_value_number):
                    if i < key_value_number + 1:
                        key_cycle_str = key_cycle_str + str(i) + ","
                    else:
                        key_cycle_str = key_cycle_str + str(i)
                key_section.append(mkey.key_name + " = " + key_cycle_str)
                key_section.new_line()
                ini_builder.append_section(key_section)

                key_number = key_number + 1

class M_IniHelperV3:

    @classmethod
    def add_switchkey_constants_section(cls,ini_builder,key_name_mkey_dict):
        '''
        声明SwitchKey的Constants变量
        '''
        if len(key_name_mkey_dict.keys()) != 0:
            constants_section = M_IniSection(M_SectionType.Constants)
            constants_section.SectionName = "Constants"
            constants_section.append("global $active" + str(M_Counter.generated_mod_number))
            for mkey in key_name_mkey_dict.values():
                key_str = "global persist " + mkey.key_name + " = " + str(mkey.initialize_value)
                constants_section.append(key_str) 

            ini_builder.append_section(constants_section)

    @classmethod
    def add_switchkey_present_section(cls,ini_builder,key_name_mkey_dict):
        '''
        声明$active激活变量
        '''
        if len(key_name_mkey_dict.keys()) != 0:
            present_section = M_IniSection(M_SectionType.Present)
            present_section.SectionName = "Present"
            present_section.append("post $active" + str(M_Counter.generated_mod_number) + " = 0")
            ini_builder.append_section(present_section)
    
    @classmethod
    def add_switchkey_sections(cls,ini_builder:M_IniBuilder,key_name_mkey_dict):
        '''
        声明按键切换和按键开关的变量 Key Section
        '''
        key_number = 0
        if len(key_name_mkey_dict.keys()) != 0:

            for mkey in key_name_mkey_dict.values():
                key_section = M_IniSection(M_SectionType.Key)
                key_section.append("[KeySwap_" + str(M_Counter.generated_mod_number) + "_" + str(key_number) + "]")
                key_section.append("condition = $active" + str(M_Counter.generated_mod_number) + " == 1")
                key_section.append("key = " + mkey.key_value)
                key_section.append("type = cycle")

                key_value_number = len(mkey.value_list)
                key_cycle_str = ""
                for i in range(key_value_number):
                    if i < key_value_number + 1:
                        key_cycle_str = key_cycle_str + str(i) + ","
                    else:
                        key_cycle_str = key_cycle_str + str(i)
                key_section.append(mkey.key_name + " = " + key_cycle_str)
                key_section.new_line()
                ini_builder.append_section(key_section)

                key_number = key_number + 1


    @classmethod
    def add_branch_key_sections(cls,ini_builder:M_IniBuilder,key_name_mkey_dict:dict[str,M_Key]):

        if len(key_name_mkey_dict.keys()) != 0:
            constants_section = M_IniSection(M_SectionType.Constants)
            constants_section.SectionName = "Constants"

            for i in range(M_Counter.generated_mod_number):
                constants_section.append("global $active" + str(i))

            for mkey in key_name_mkey_dict.values():
                key_str = "global persist " + mkey.key_name + " = " + str(mkey.initialize_value)
                constants_section.append(key_str) 

            ini_builder.append_section(constants_section)


        if len(key_name_mkey_dict.keys()) != 0:
            present_section = M_IniSection(M_SectionType.Present)
            present_section.SectionName = "Present"

            for i in range(M_Counter.generated_mod_number):
                present_section.append("post $active" + str(i) + " = 0")
            ini_builder.append_section(present_section)


        # TODO 这里的condition = 有一定的几率和声明的active对不上。

        key_number = 0
        if len(key_name_mkey_dict.keys()) != 0:

            for mkey in key_name_mkey_dict.values():
                key_section = M_IniSection(M_SectionType.Key)
                key_section.append("[KeySwap_" + str(key_number) + "]")
                # key_section.append("condition = $active" + str(key_number) + " == 1")

                # XXX 这里由于有BUG，我们固定用$active0来检测激活，不搞那么复杂了。
                key_section.append("condition = $active0 == 1")

                if mkey.initialize_vk_str != "":
                    key_section.append("key = " + mkey.initialize_vk_str)
                else:
                    key_section.append("key = " + mkey.key_value)
                key_section.append("type = cycle")

                key_value_number = len(mkey.value_list)
                key_cycle_str = ""
                for i in range(key_value_number):
                    if i < key_value_number + 1:
                        key_cycle_str = key_cycle_str + str(i) + ","
                    else:
                        key_cycle_str = key_cycle_str + str(i)
                key_section.append(mkey.key_name + " = " + key_cycle_str)
                key_section.new_line()
                ini_builder.append_section(key_section)

                key_number = key_number + 1