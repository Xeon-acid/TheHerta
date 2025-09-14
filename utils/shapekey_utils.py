
import bpy
import time
import numpy
import re
from mathutils import Vector

from .timer_utils import TimerUtils
from typing import List, Tuple, Dict, Optional

class ShapeKeyUtils:
    # Github: https://github.com/przemir/ApplyModifierForObjectWithShapeKeys

    @classmethod
    def apply_modifiers_for_object_with_shape_keys(cls,context, selectedModifiers, disable_armatures):
        # ------------------------------------------------------------------------------
        # The MIT License (MIT)
        #
        # Copyright (c) 2015 Przemysław Bągard
        #
        # Permission is hereby granted, free of charge, to any person obtaining a copy
        # of this software and associated documentation files (the "Software"), to deal
        # in the Software without restriction, including without limitation the rights
        # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        # copies of the Software, and to permit persons to whom the Software is
        # furnished to do so, subject to the following conditions:
        #
        # The above copyright notice and this permission notice shall be included in
        # all copies or substantial portions of the Software.
        #
        # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
        # THE SOFTWARE.
        # ------------------------------------------------------------------------------

        # Date: 01 February 2015
        # Blender script
        # Description: Apply modifier and remove from the stack for object with shape keys
        # (Pushing 'Apply' button in 'Object modifiers' tab result in an error 'Modifier cannot be applied to a mesh with shape keys').

        # Algorithm (old):
        # - Duplicate active object as many times as the number of shape keys
        # - For each copy remove all shape keys except one
        # - Removing last shape does not change geometry data of object
        # - Apply modifier for each copy
        # - Join objects as shapes and restore shape keys names
        # - Delete all duplicated object except one
        # - Delete old object
        # Original object should be preserved (to keep object name and other data associated with object/mesh). 

        # Algorithm (new):
        # Don't make list of copies, handle it one shape at time.
        # In this algorithm there shouldn't be more than 3 copy of object at time, so it should be more memory-friendly.
        #
        # - Copy object which will hold shape keys
        # - For original object (which will be also result object), remove all shape keys, then apply modifiers. Add "base" shape key
        # - For each shape key except base copy temporary object from copy. Then for temporaryObject:
        #     - remove all shape keys except one (done by removing all shape keys, then transfering the right one from copyObject)
        #     - apply modifiers
        #     - merge with originalObject
        #     - delete temporaryObject
        # - Delete copyObject.
        
        if len(selectedModifiers) == 0:
            return

        list_properties = []
        properties = ["interpolation", "mute", "name", "relative_key", "slider_max", "slider_min", "value", "vertex_group"]
        shapesCount = 0
        vertCount = -1
        startTime = time.time()
        
        # Inspect modifiers for hints used in error message if needed.
        contains_mirror_with_merge = False
        for modifier in context.object.modifiers:
            if modifier.name in selectedModifiers:
                if modifier.type == 'MIRROR' and modifier.use_mirror_merge == True:
                    contains_mirror_with_merge = True

        # Disable armature modifiers.
        disabled_armature_modifiers = []
        if disable_armatures:
            for modifier in context.object.modifiers:
                if modifier.name not in selectedModifiers and modifier.type == 'ARMATURE' and modifier.show_viewport == True:
                    disabled_armature_modifiers.append(modifier)
                    modifier.show_viewport = False
        
        # Calculate shape keys count.
        if context.object.data.shape_keys:
            shapesCount = len(context.object.data.shape_keys.key_blocks)
        
        # If there are no shape keys, just apply modifiers.
        if(shapesCount == 0):
            for modifierName in selectedModifiers:
                bpy.ops.object.modifier_apply(modifier=modifierName)
            return (True, None)
        
        # We want to preserve original object, so all shapes will be joined to it.
        originalObject = context.view_layer.objects.active
        bpy.ops.object.select_all(action='DESELECT')
        originalObject.select_set(True)
        
        # Copy object which will holds all shape keys.
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        copyObject = context.view_layer.objects.active
        copyObject.select_set(False)
        
        # Return selection to originalObject.
        context.view_layer.objects.active = originalObject
        originalObject.select_set(True)
        
        # Save key shape properties
        for i in range(0, shapesCount):
            key_b = originalObject.data.shape_keys.key_blocks[i]
            print (originalObject.data.shape_keys.key_blocks[i].name, key_b.name)
            properties_object = {p:None for p in properties}
            properties_object["name"] = key_b.name
            properties_object["mute"] = key_b.mute
            properties_object["interpolation"] = key_b.interpolation
            properties_object["relative_key"] = key_b.relative_key.name
            properties_object["slider_max"] = key_b.slider_max
            properties_object["slider_min"] = key_b.slider_min
            properties_object["value"] = key_b.value
            properties_object["vertex_group"] = key_b.vertex_group
            list_properties.append(properties_object)

        # Handle base shape in "originalObject"
        print("applyModifierForObjectWithShapeKeys: Applying base shape key")
        bpy.ops.object.shape_key_remove(all=True)
        for modifierName in selectedModifiers:
            bpy.ops.object.modifier_apply(modifier=modifierName)
        vertCount = len(originalObject.data.vertices)
        bpy.ops.object.shape_key_add(from_mix=False)
        originalObject.select_set(False)
        
        # Handle other shape-keys: copy object, get right shape-key, apply modifiers and merge with originalObject.
        # We handle one object at time here.
        for i in range(1, shapesCount):
            currTime = time.time()
            elapsedTime = currTime - startTime

            print("applyModifierForObjectWithShapeKeys: Applying shape key %d/%d ('%s', %0.2f seconds since start)" % (i+1, shapesCount, list_properties[i]["name"], elapsedTime))
            context.view_layer.objects.active = copyObject
            copyObject.select_set(True)
            
            # Copy temp object.
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            tmpObject = context.view_layer.objects.active
            bpy.ops.object.shape_key_remove(all=True)
            copyObject.select_set(True)
            copyObject.active_shape_key_index = i
            
            # Get right shape-key.
            bpy.ops.object.shape_key_transfer()
            context.object.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove()
            bpy.ops.object.shape_key_remove(all=True)
            
            # Time to apply modifiers.
            for modifierName in selectedModifiers:
                bpy.ops.object.modifier_apply(modifier=modifierName)
            
            # Verify number of vertices.
            if vertCount != len(tmpObject.data.vertices):
            
                errorInfoHint = ""
                if contains_mirror_with_merge == True:
                    errorInfoHint = "There is mirror modifier with 'Merge' property enabled. This may cause a problem."
                if errorInfoHint:
                    errorInfoHint = "\n\nHint: " + errorInfoHint
                errorInfo = ("Shape keys ended up with different number of vertices!\n"
                            "All shape keys needs to have the same number of vertices after modifier is applied.\n"
                            "Otherwise joining such shape keys will fail!%s" % errorInfoHint)
                return (False, errorInfo)
        
            # Join with originalObject
            copyObject.select_set(False)
            context.view_layer.objects.active = originalObject
            originalObject.select_set(True)
            bpy.ops.object.join_shapes()
            originalObject.select_set(False)
            context.view_layer.objects.active = tmpObject
            
            # Remove tmpObject
            tmpMesh = tmpObject.data
            bpy.ops.object.delete(use_global=False)
            bpy.data.meshes.remove(tmpMesh)
        
        # Restore shape key properties like name, mute etc.
        context.view_layer.objects.active = originalObject
        for i in range(0, shapesCount):
            key_b = context.view_layer.objects.active.data.shape_keys.key_blocks[i]
            # name needs to be restored before relative_key
            key_b.name = list_properties[i]["name"]
            
        for i in range(0, shapesCount):
            key_b = context.view_layer.objects.active.data.shape_keys.key_blocks[i]
            key_b.interpolation = list_properties[i]["interpolation"]
            key_b.mute = list_properties[i]["mute"]
            key_b.slider_max = list_properties[i]["slider_max"]
            key_b.slider_min = list_properties[i]["slider_min"]
            key_b.value = list_properties[i]["value"]
            key_b.vertex_group = list_properties[i]["vertex_group"]
            rel_key = list_properties[i]["relative_key"]
        
            for j in range(0, shapesCount):
                key_brel = context.view_layer.objects.active.data.shape_keys.key_blocks[j]
                if rel_key == key_brel.name:
                    key_b.relative_key = key_brel
                    break
        
        # Remove copyObject.
        originalObject.select_set(False)
        context.view_layer.objects.active = copyObject
        copyObject.select_set(True)
        tmpMesh = copyObject.data
        bpy.ops.object.delete(use_global=False)
        bpy.data.meshes.remove(tmpMesh)
        
        # Select originalObject.
        context.view_layer.objects.active = originalObject
        context.view_layer.objects.active.select_set(True)
        
        if disable_armatures:
            for modifier in disabled_armature_modifiers:
                modifier.show_viewport = True
        
        return (True, None)


    @classmethod
    def extract_shapekey_data(cls,merged_obj,index_vertex_id_dict):
        '''
        传入一个Obj，提取出其形态键数据为特定格式
        '''
        TimerUtils.Start("process shapekey data")

        shapekey_cache = cls.get_shapekey_cache(merged_obj,index_vertex_id_dict)

        shapekey_offsets = []
        shapekey_vertex_ids = []
        shapekey_vertex_offsets = []

        # 从0到128去获取ShapeKey的Index，有就直接加到
        shapekey_verts_count = 0
        for group_id in range(128):
            shapekey = shapekey_cache.get(group_id, None)

            if shapekey is None or len(shapekey_cache[group_id]) == 0:
                shapekey_offsets.extend([shapekey_verts_count if shapekey_verts_count != 0 else 0])
                continue

            shapekey_offsets.extend([shapekey_verts_count])

            for draw_index, vertex_offsets in shapekey.items():
                shapekey_vertex_ids.extend([draw_index])
                shapekey_vertex_offsets.extend(vertex_offsets + [0, 0, 0])
                shapekey_verts_count += 1

        TimerUtils.End("process shapekey data") 
        return shapekey_offsets,shapekey_vertex_ids,shapekey_vertex_offsets
    


    @classmethod
    def get_shapekey_cache(cls, merged_obj, index_vertex_id_dict):
        '''
        Numpy优化版本，快很多
        '''
        # TimerUtils.Start("shapekey_cache")
        obj = merged_obj
        mesh = obj.data
        mesh_shapekeys = mesh.shape_keys
        
        if mesh_shapekeys is None:
            print(f"obj: {obj.name} 不含有形态键，跳过处理")
            TimerUtils.End("shapekey_cache")
            return None, None, None

        # 构建顶点索引到全局index_id的反向映射
        vertex_to_indices = {}
        for index_id, vertex_id in index_vertex_id_dict.items():
            if vertex_id not in vertex_to_indices:
                vertex_to_indices[vertex_id] = []
            vertex_to_indices[vertex_id].append(index_id)

        # 获取基础坐标
        base_data = mesh_shapekeys.key_blocks['Basis'].data
        base_coords = numpy.empty((len(mesh.vertices), 3), dtype=numpy.float32)
        base_data.foreach_get('co', base_coords.ravel())

        shapekey_cache = {}
        shapekey_pattern = re.compile(r'.*(?:deform|custom)[_ -]*(\d+).*')

        # TODO 这里的形态键是不是忘了排序？这里不排序是否影响？
        # 处理每个形态键
        for shapekey in mesh_shapekeys.key_blocks:
            # 跳过基础形态键
            if shapekey.name == 'Basis':
                continue
            
            # print(shapekey.name)

            # 提取形态键ID
            match = shapekey_pattern.findall(shapekey.name.lower())
            if not match:
                print(f"当前形态键名称:{shapekey.name} 不符合命名规范，跳过")
                continue
                
            shapekey_idx = int(match[0])
            # print("process: " + str(shapekey_idx))
            if shapekey_idx >= 128:
                break  # 按原逻辑遇到>=128的索引直接停止处理

            # 获取形态键坐标数据
            sk_coords = numpy.empty((len(mesh.vertices), 3), dtype=numpy.float32)
            shapekey.data.foreach_get('co', sk_coords.ravel())
            
            # 计算偏移量 (向量化操作)
            offsets = sk_coords - base_coords
            
            # 计算向量长度并过滤小偏移
            lengths = numpy.linalg.norm(offsets, axis=1)
            valid_mask = lengths >= 1e-9
            valid_vertex_ids = numpy.where(valid_mask)[0]
            
            if not valid_vertex_ids.size:
                # 这里一般不会触发
                # print("valid_vertex_ids.size not, continue!")
                continue
                
            # 按形态键初始化缓存
            if shapekey_idx not in shapekey_cache:
                shapekey_cache[shapekey_idx] = {}
                
            # 处理有效顶点
            for v_idx in valid_vertex_ids:
                offset_list = offsets[v_idx].tolist()
                # 获取关联的全局index_id
                if v_idx in vertex_to_indices:
                    for index_id in vertex_to_indices[v_idx]:
                        shapekey_cache[shapekey_idx][index_id] = offset_list

        # TimerUtils.End("shapekey_cache")
        return shapekey_cache
    

    @classmethod
    def extract_shapekey_data_v2(cls, merged_obj, index_vertex_id_dict):
        '''
        旧代码分成俩不好理解，所以整合成了一个，方便理解。
        传入一个 Obj，直接输出形态键三数组（功能与旧代码完全一致）
        耗时大概0.6秒
        '''
        TimerUtils.Start("process shapekey data")
        mesh = merged_obj.data
        shapekeys = mesh.shape_keys
        if not shapekeys:
            TimerUtils.End("process shapekey data")
            return [0] * 128, [], []

        # ----- 1. vertex_id -> [draw_index,...] 反向表
        v2d = {}
        for draw_idx, v_idx in index_vertex_id_dict.items():
            v2d.setdefault(v_idx, []).append(draw_idx)

        # ----- 2. 读 Basis
        basis = numpy.empty((len(mesh.vertices), 3), dtype=numpy.float32)
        shapekeys.key_blocks['Basis'].data.foreach_get('co', basis.ravel())

        # ----- 3. 正则
        pat = re.compile(r'.*(?:deform|custom)[_ -]*(\d+).*', re.I)

        # ----- 4. 先按 0-127 顺序收集每键“顶点集”，后者覆盖前者
        # key=shape_idx  value={draw_index: [dx,dy,dz], ...}
        cache = {}
        for sk in shapekeys.key_blocks:
            if sk.name == 'Basis':
                continue
            m = pat.findall(sk.name)
            if not m:
                continue
            idx = int(m[0])
            if idx >= 128:
                continue

            skco = numpy.empty((len(mesh.vertices), 3), dtype=numpy.float32)
            sk.data.foreach_get('co', skco.ravel())
            delta = skco - basis
            mask = numpy.linalg.norm(delta, axis=1) >= 1e-9
            valid_v = numpy.where(mask)[0]

            # 后者整键覆盖
            cache[idx] = {}
            for v_idx in valid_v:
                off = delta[v_idx].tolist()
                for draw_idx in v2d.get(v_idx, []):
                    cache[idx][draw_idx] = off

        # ----- 5. 按 0-127 顺序拼三数组（前缀和版）
        shapekey_offsets = []
        shapekey_vertex_ids = []
        shapekey_vertex_offsets = []
        verts_so_far = 0

        for group_id in range(128):
            if group_id in cache and cache[group_id]:
                shapekey_offsets.append(verts_so_far)
                for draw_idx, off in cache[group_id].items():
                    shapekey_vertex_ids.append(draw_idx)
                    shapekey_vertex_offsets.extend(off + [0., 0., 0.])
                    verts_so_far += 1
            else:
                shapekey_offsets.append(verts_so_far)

        TimerUtils.End("process shapekey data")
        return shapekey_offsets, shapekey_vertex_ids, shapekey_vertex_offsets