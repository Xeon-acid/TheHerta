import os
import bpy
import json
import subprocess
from ..config.main_config import *
from .json_utils import *
from .format_utils import Fatal


class DrawIBPair:

    def __init__(self):
        self.DrawIB = ""
        self.AliasName = ""


class ConfigUtils:

    '''
    This is a ini generate helper class to reuse functions.
    '''
    key_list = ["x","c","v","b","n","m","j","k","l","o","p","[","]",
                "x","c","v","b","n","m","j","k","l","o","p","[","]",
                "x","c","v","b","n","m","j","k","l","o","p","[","]"]

    @classmethod
    def get_mod_switch_key(cls,key_index:int):
        '''
        Default mod switch/toggle key.
        '''
        
        # 尝试读取Setting.json里的设置，解析错误就还使用默认的
        try:
            setting_json_dict = JsonUtils.LoadFromFile(GlobalConfig.path_main_json())
            print(setting_json_dict)
            mod_switch_key = str(setting_json_dict["ModSwitchKey"])
            mod_switch_key_list = mod_switch_key.split(",")
            print(mod_switch_key_list)
            switch_key_list:list[str] = []
            for switch_key_str in mod_switch_key_list:
                switch_key_list.append(switch_key_str[1:-1])
            cls.key_list = switch_key_list
        except Exception:
            print("解析自定义SwitchKey失败")

        return cls.key_list[key_index]

    @classmethod
    def get_extract_drawib_list_from_workspace_config_json(cls) -> list[DrawIBPair]:
        '''
        从当前工作空间的Config.json中读取DrawIB列表
        '''
        workspace_path = GlobalConfig.path_workspace_folder()

        game_config_path = os.path.join(workspace_path,"Config.json")
        game_config_json = JsonUtils.LoadFromFile(game_config_path)
 
        draw_ib_list = []
        for item in game_config_json:
            drawib_pair = DrawIBPair()

            drawib_pair.DrawIB =  item["DrawIB"]
            drawib_pair.AliasName = item["Alias"]

            draw_ib_list.append(drawib_pair)

        return draw_ib_list
    
    @classmethod
    def get_draw_ib_alias_name_dict(cls):

        draw_ib_alias_name_dict = {}
        draw_ib_pair_list= ConfigUtils.get_extract_drawib_list_from_workspace_config_json()
        for draw_ib_pair in draw_ib_pair_list:
            draw_ib_alias_name_dict[draw_ib_pair.DrawIB] = draw_ib_pair.AliasName

        return draw_ib_alias_name_dict


    @classmethod
    def get_import_drawib_aliasname_folder_path_dict_with_first_match_type(cls)->list:
        output_folder_path = GlobalConfig.path_workspace_folder()
        
        draw_ib_list= ConfigUtils.get_extract_drawib_list_from_workspace_config_json()
        
        final_import_folder_path_dict = {}

        for draw_ib_pair in draw_ib_list:
            draw_ib = draw_ib_pair.DrawIB
            alias_name = draw_ib_pair.AliasName

            gpu_import_folder_path_list = []
            cpu_import_folder_path_list = []

            # print("DrawIB:", draw_ib)
            import_drawib_folder_path = os.path.join(output_folder_path, draw_ib)

            if not os.path.exists(import_drawib_folder_path):
                continue

            dirs = os.listdir(import_drawib_folder_path)
            for dirname in dirs:
                if not dirname.startswith("TYPE_"):
                    continue
                final_import_folder_path = os.path.join(import_drawib_folder_path,dirname)
                if dirname.startswith("TYPE_GPU"):
                    gpu_import_folder_path_list.append(final_import_folder_path)
                elif dirname.startswith("TYPE_CPU"):
                    cpu_import_folder_path_list.append(final_import_folder_path)

            if len(gpu_import_folder_path_list) != 0:
                final_import_folder_path_dict[draw_ib + "_" + alias_name] = gpu_import_folder_path_list[0]
            elif len(cpu_import_folder_path_list) != 0:
                final_import_folder_path_dict[draw_ib + "_" + alias_name] = cpu_import_folder_path_list[0]
            else:
                pass

        return final_import_folder_path_dict


    @classmethod
    def get_prefix_list_from_tmp_json(cls,import_folder_path:str) ->list:
        '''
        从tmp.json中读取要从工作空间中一键导入的模型的名称前缀
        '''
        tmp_json_path = os.path.join(import_folder_path, "tmp.json")

        drawib = os.path.basename(import_folder_path)

        if os.path.exists(tmp_json_path):
            tmp_json_file = open(tmp_json_path)
            tmp_json = json.load(tmp_json_file)
            tmp_json_file.close()
            import_prefix_list = tmp_json["ImportModelList"]
            if len(import_prefix_list) == 0:
                import_partname_prefix_list = []
                partname_list = tmp_json["PartNameList"]
                for partname in partname_list:
                    import_partname_prefix_list.append(drawib + "-" + partname)
                return import_partname_prefix_list
            else:
                # import_prefix_list.sort() it's naturally sorted in DBMT so we don't need sort here.
                return import_prefix_list
        else:
            return []
    

    @classmethod
    def read_tmp_json(cls,import_folder_path:str) ->dict:
        tmp_json_path = os.path.join(import_folder_path, "tmp.json")
        if os.path.exists(tmp_json_path):
            tmp_json_file = open(tmp_json_path)
            tmp_json = json.load(tmp_json_file)
            tmp_json_file.close()
            return tmp_json
        else:
            raise Fatal("Target tmp.json didn't exists: " + tmp_json_path)


    # Read model prefix attribute in fmt file to locate .ib and .vb file.
    # Save lots of space when reverse mod which have same stride but different kinds of D3D11GameType.
    @classmethod
    def get_model_prefix_from_fmt_file(cls,fmt_file_path:str)->str:
        with open(fmt_file_path, 'r') as file:
            for i in range(10):  
                line = file.readline().strip()
                if not line:
                    continue
                if line.startswith('prefix:'):
                    return line.split(':')[1].strip()  
        return ""  


    