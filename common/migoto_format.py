import json
import io

import numpy
import os

from ..utils.format_utils import FormatUtils, Fatal
from dataclasses import dataclass, field, asdict
from ..utils.log_utils import LOG


from ..utils.format_utils import *
from ..utils.format_utils import *
from ..config.main_config import *
from ..utils.timer_utils import *

from typing import List, Dict, Union
from pathlib import Path

from ..utils.format_utils import *


from dataclasses import dataclass, field, asdict


@dataclass
class D3D11Element:
    SemanticName:str
    SemanticIndex:int
    Format:str
    ByteWidth:int = field(default=0,init=False)
    # Which type of slot and slot number it use? eg:vb0
    ExtractSlot:str
    # Is it from pointlist or trianglelist or compute shader?
    ExtractTechnique:str
    # Human named category, also will be the buf file name suffix.
    Category:str

    # Fixed items
    InputSlot:str = field(default="0", init=False, repr=False)
    InputSlotClass:str = field(default="per-vertex", init=False, repr=False)
    InstanceDataStepRate:str = field(default="0", init=False, repr=False)

    # Generated Items
    ElementNumber:int = field(init=False,default=0)
    AlignedByteOffset:int
    ElementName:str = field(init=False,default="")

    def __post_init__(self):
        self.ElementName = self.get_indexed_semantic_name()

    def get_indexed_semantic_name(self)->str:
        if self.SemanticIndex == 0:
            return self.SemanticName
        else:
            return self.SemanticName + str(self.SemanticIndex)

class FMTFile:
    def __init__(self, fmt_file_path:str):
        self.stride = 0
        self.topology = ""
        self.format = ""
        self.gametypename = ""
        self.prefix = ""
        self.scale = "1.0"
        self.rotate_angle:bool = False
        self.rotate_angle_x:float = 0
        self.rotate_angle_y:float = 0
        self.rotate_angle_z:float = 0
        self.flip_face_orientation:bool = False

        self.elements:list[D3D11Element] = []

        with open(fmt_file_path, 'r') as file:
            lines = file.readlines()

        element_info = {}
        for line in lines:
            parts = line.strip().split(":")
            if len(parts) < 2:
                continue  # 跳过格式不正确的行

            key, value = parts[0].strip(), ":".join(parts[1:]).strip()
            if key == "stride":
                self.stride = int(value)
            elif key == "topology":
                self.topology = value
            elif key == "format":
                self.format = value
            elif key == "gametypename":
                self.gametypename = value
            elif key == "prefix":
                self.prefix = value
            elif key == "scale":
                self.scale = value
            elif key == "rotate_angle":
                self.rotate_angle = value.lower() == "true"
            elif key == "rotate_angle_x":
                self.rotate_angle_x = float(value)
            elif key == "rotate_angle_y":
                self.rotate_angle_y = float(value)
            elif key == "rotate_angle_z":
                self.rotate_angle_z = float(value)
            

            
            elif key == "flip_face_orientation":
                self.flip_face_orientation = value.lower() == "true"

            elif key.startswith("element"):
                # 处理element块
                if "SemanticName" in element_info:
                    append_d3delement = D3D11Element(
                        SemanticName=element_info["SemanticName"], SemanticIndex=int(element_info["SemanticIndex"]),
                        Format= element_info["Format"],AlignedByteOffset= int(element_info["AlignedByteOffset"]),
                        ExtractSlot="0",ExtractTechnique="",Category="")
                    
                    if "ByteWidth" in element_info:
                        # print("读取到ByteWidth存在: " + element_info["ByteWidth"])
                        append_d3delement.ByteWidth = int(element_info["ByteWidth"])
                    else:
                        append_d3delement.ByteWidth = FormatUtils.format_size(append_d3delement.Format)
                    
                    # 如果已经有一个element信息，则先添加到列表中
                    self.elements.append(append_d3delement)
                    element_info.clear()  # 清空当前element信息

                # 将新的element属性添加到element_info字典中
                element_info[key.split()[0]] = value
            elif key in ["SemanticName", "SemanticIndex", "Format","ByteWidth", "InputSlot", "AlignedByteOffset", "InputSlotClass", "InstanceDataStepRate"]:
                element_info[key] = value

        # 添加最后一个element
        if "SemanticName" in element_info:
            append_d3delement = D3D11Element(
                SemanticName=element_info["SemanticName"], SemanticIndex=int(element_info["SemanticIndex"]),
                Format= element_info["Format"],AlignedByteOffset= int(element_info["AlignedByteOffset"]),
                ExtractSlot="0",ExtractTechnique="",Category=""
            )

            if "ByteWidth" in element_info:
                # print("读取到ByteWidth存在: " + element_info["ByteWidth"])
                append_d3delement.ByteWidth = int(element_info["ByteWidth"])
            else:
                append_d3delement.ByteWidth = FormatUtils.format_size(append_d3delement.Format)

            self.elements.append(append_d3delement)

            

    def __repr__(self):
        return (f"FMTFile(stride={self.stride}, topology='{self.topology}', format='{self.format}', "
                f"gametypename='{self.gametypename}', prefix='{self.prefix}', elements={self.elements})")
    
    def get_dtype(self):
        fields = []
        for elemnt in self.elements:
            # Numpy类型由Format决定，此时即使是WWMI的特殊R8_UINT也能得到正确的numpy.uint8
            numpy_type = FormatUtils.get_nptype_from_format(elemnt.Format)

            # 这里我们用ByteWidth / numpy_type.itemsize 得到总的维度数量，也就是列数
            size = int( elemnt.ByteWidth / numpy.dtype(numpy_type).itemsize)

            # print("element: "+ elemnt.ElementName)
            # print(numpy_type)
            # print(size)
            fields.append((elemnt.ElementName,numpy_type , size))
        dtype = numpy.dtype(fields)
        return dtype
    


class MigotoBinaryFile:

    '''
    3Dmigoto模型文件

    暂时还没有更好的设计，暂时先沿用旧的ib vb fmt设计
    
    prefix是前缀，比如Body.ib Body.vb Body.fmt 那么此时Body就是prefix
    location_folder_path是存放这些文件的文件夹路径，比如当前工作空间中提取的对应数据类型文件夹

    '''
    def __init__(self, fmt_path:str, mesh_name:str = ""):
        self.fmt_file = FMTFile(fmt_path)
        print("fmt_path: " + fmt_path)
        location_folder_path = os.path.dirname(fmt_path)
        print("location_folder_path: " + location_folder_path)

        if self.fmt_file.prefix == "":
            self.fmt_file.prefix = os.path.basename(fmt_path).split(".fmt")[0]

        if mesh_name == "":
            self.mesh_name = self.fmt_file.prefix
        else:
            self.mesh_name = mesh_name
        

        print("prefix: " + self.fmt_file.prefix)
        self.init_from_prefix(self.fmt_file.prefix, location_folder_path)

    def init_from_prefix(self,prefix:str, location_folder_path:str):

        self.fmt_name = prefix + ".fmt"
        self.vb_name = prefix + ".vb"
        self.ib_name = prefix + ".ib"

        self.location_folder_path = location_folder_path

        self.vb_bin_path = os.path.join(location_folder_path, self.vb_name)
        self.ib_bin_path = os.path.join(location_folder_path, self.ib_name)
        self.fmt_path = os.path.join(location_folder_path, self.fmt_name)

        self.file_sanity_check()

        self.vb_file_size = os.path.getsize(self.vb_bin_path)
        self.ib_file_size = os.path.getsize(self.ib_bin_path)

        self.init_data()

    def init_data(self):
        ib_stride = FormatUtils.format_size(self.fmt_file.format)

        self.ib_count = int(self.ib_file_size / ib_stride)
        self.ib_polygon_count = int(self.ib_count / 3)
        self.ib_data = numpy.fromfile(self.ib_bin_path, dtype=FormatUtils.get_nptype_from_format(self.fmt_file.format), count=self.ib_count)
        
        # 读取fmt文件，解析出后面要用的dtype
        fmt_dtype = self.fmt_file.get_dtype()
        vb_stride = fmt_dtype.itemsize

        self.vb_vertex_count = int(self.vb_file_size / vb_stride)
        self.vb_data = numpy.fromfile(self.vb_bin_path, dtype=fmt_dtype, count=self.vb_vertex_count)

    
    def file_sanity_check(self):
        '''
        检查对应文件是否存在，不存在则抛出异常
        三个文件，必须都存在，缺一不可
        '''
        if not os.path.exists(self.vb_bin_path):
            raise Fatal("Unable to find matching .vb file for : " + self.mesh_name)
        if not os.path.exists(self.ib_bin_path):
            raise Fatal("Unable to find matching .ib file for : " + self.mesh_name)
        # if not os.path.exists(self.fmt_path):
        #     raise Fatal("Unable to find matching .fmt file for : " + self.mesh_name)

    def file_size_check(self) -> bool:
        '''
        检查.ib和.vb文件是否为空，如果为空则弹出错误提醒信息，但不报错。
        '''
        # 如果vb和ib文件不存在，则跳过导入
        # 我们不能直接抛出异常，因为有些.ib文件是空的占位文件
        if self.vb_file_size == 0:
            LOG.warning("Current Import " + self.vb_name +" file is empty, skip import.")
            return False
        
        if self.ib_file_size == 0:
            LOG.warning("Current Import " + self.ib_name + " file is empty, skip import.")
            return False
        
        return True

class TextureReplace:
    def  __init__(self):
        self.resource_name = ""
        self.filter_index = 0
        self.hash = ""
        self.style = ""

class M_DrawIndexed:
    def __init__(self) -> None:
        self.DrawNumber = ""

        # 绘制起始位置
        self.DrawOffsetIndex = "" 

        self.DrawStartIndex = "0"

        # 代表一个obj具体的draw_indexed
        self.AliasName = "" 

        # 代表这个obj的顶点数
        self.UniqueVertexCount = 0 
    
    def get_draw_str(self) ->str:
        return "drawindexed = " + self.DrawNumber + "," + self.DrawOffsetIndex +  "," + self.DrawStartIndex

class M_Key:
    '''
    key_name 声明的key名称，一般按照声明顺序为$swapkey + 数字
    key_value 具体的按键VK值
    '''

    def __init__(self):
        self.key_name = ""
        self.key_value = ""
        self.value_list:list[int] = []
        
        self.initialize_value = 0
        self.initialize_vk_str = "" # 虚拟按键组合，遵循3Dmigoto的解析格式

        # 用于chain_key_list中传递使用，
        self.tmp_value = 0

    def __str__(self):
        return (f"M_Key(key_name='{self.key_name}', key_value='{self.key_value}', "
                f"value_list={self.value_list}, initialize_value={self.initialize_value}, "
                f"tmp_value={self.tmp_value})")
    
class M_Condition:
    '''
    
    '''
    def __init__(self,work_key_list:list[M_Key] = []):
        self.work_key_list = work_key_list

        # 计算出生效的ConditionStr
        condition_str = ""
        if len(self.work_key_list) != 0:
            for work_key in self.work_key_list:
                single_condition:str = work_key.key_name + " == " + str(work_key.tmp_value)
                condition_str = condition_str + single_condition + " && "
            # 移除结尾的最后四个字符 " && "
            condition_str = condition_str[:-4] 
        
        self.condition_str = condition_str


class ObjDataModel:
    def __init__(self,obj_name:str):
        self.obj_name = obj_name
        
        # 因为现在的obj都需要遵守命名规则
        obj_name_split = self.obj_name.split("-")
        self.draw_ib = obj_name_split[0]
        self.component_count = int(obj_name_split[1])
        self.obj_alias_name = obj_name_split[2]

        # 其它属性
        self.ib = []
        self.category_buffer_dict = {}
        self.index_vertex_id_dict = {} # 仅用于WWMI的索引顶点ID字典，key是顶点索引，value是顶点ID，默认可以为None
        self.condition:M_Condition = M_Condition()
        self.drawindexed_obj:M_DrawIndexed = M_DrawIndexed()


class DrawIBItem:
    def __init__(self):
        self.draw_ib = "" # DrawIB 是8位的 IndexBuffer的Hash值
        self.alias_name = "" # Alias 是DrawIB的别名，起标识符作用

# Designed to read from json file for game type config
@dataclass
class D3D11GameType:
    # Read config from json file, easy to modify and test.
    FilePath:str = field(repr=False)

    # Original file name.
    FileName:str = field(init=False,repr=False)
    # The name of the game type, usually the filename without suffix.
    GameTypeName:str = field(init=False)
    # Is GPU-PreSkinning or CPU-PreSkinning
    GPU_PreSkinning:bool = field(init=False,default=False)
    # All d3d11 element,should be already ordered in config json.
    D3D11ElementList:list[D3D11Element] = field(init=False,repr=False)
    # Ordered ElementName list.
    OrderedFullElementList:list[str] = field(init=False,repr=False)
    # 按顺序排列的CategoryName
    OrderedCategoryNameList:list[str] = field(init=False,repr=False)
    # Category name and draw category name, used to decide the category should draw on which category's TextureOverrideVB.
    CategoryDrawCategoryDict:Dict[str,str] = field(init=False,repr=False)


    # Generated
    ElementNameD3D11ElementDict:Dict[str,D3D11Element] = field(init=False,repr=False)
    CategoryExtractSlotDict:Dict[str,str] =  field(init=False,repr=False)
    CategoryExtractTechniqueDict:Dict[str,str] =  field(init=False,repr=False)
    CategoryStrideDict:Dict[str,int] =  field(init=False,repr=False)

    def __post_init__(self):
        self.FileName = os.path.basename(self.FilePath)
        self.GameTypeName = os.path.splitext(self.FileName)[0]
        

        self.OrderedFullElementList = []
        self.OrderedCategoryNameList = []
        self.D3D11ElementList = []

        self.CategoryDrawCategoryDict = {}
        self.CategoryExtractSlotDict = {}
        self.CategoryExtractTechniqueDict = {}
        self.CategoryStrideDict = {}
        self.ElementNameD3D11ElementDict = {}

        # read config from json file.
        with open(self.FilePath, 'r', encoding='utf-8') as f:
            game_type_json = json.load(f)
        
        self.GPU_PreSkinning = game_type_json.get("GPU-PreSkinning",False)

        self.GameTypeName = game_type_json.get("WorkGameType","")

        # self.OrderedFullElementList = game_type_json.get("OrderedFullElementList",[])
        self.CategoryDrawCategoryDict = game_type_json.get("CategoryDrawCategoryMap",{})
        d3d11_element_list_json = game_type_json.get("D3D11ElementList",[])
        aligned_byte_offset = 0
        for d3d11_element_json in d3d11_element_list_json:
            d3d11_element = D3D11Element(
                SemanticName=d3d11_element_json.get("SemanticName",""),
                SemanticIndex=int(d3d11_element_json.get("SemanticIndex","")),
                Format=d3d11_element_json.get("Format",""),
                ByteWidth=int(d3d11_element_json.get("ByteWidth",0)),
                ExtractSlot=d3d11_element_json.get("ExtractSlot",""),
                ExtractTechnique=d3d11_element_json.get("ExtractTechnique",""),
                Category=d3d11_element_json.get("Category",""),
                AlignedByteOffset=aligned_byte_offset
            )
            aligned_byte_offset = aligned_byte_offset + d3d11_element.ByteWidth
            self.D3D11ElementList.append(d3d11_element)

            # 这俩常用
            self.OrderedFullElementList.append(d3d11_element.get_indexed_semantic_name())
            if d3d11_element.Category not in self.OrderedCategoryNameList:
                self.OrderedCategoryNameList.append(d3d11_element.Category)
        
        for d3d11_element in self.D3D11ElementList:
            self.CategoryExtractSlotDict[d3d11_element.Category] = d3d11_element.ExtractSlot
            self.CategoryExtractTechniqueDict[d3d11_element.Category] = d3d11_element.ExtractTechnique
            self.CategoryStrideDict[d3d11_element.Category] = self.CategoryStrideDict.get(d3d11_element.Category,0) + d3d11_element.ByteWidth
            self.ElementNameD3D11ElementDict[d3d11_element.ElementName] = d3d11_element
    
    def get_real_category_stride_dict(self) -> dict:
        new_dict = {}
        for categoryname,category_stride in self.CategoryStrideDict.items():
            new_dict[categoryname] = category_stride
        return new_dict

  
