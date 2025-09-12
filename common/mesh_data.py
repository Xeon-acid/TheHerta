import numpy
import bpy


class MeshData:
    '''
    MeshClass用于获取每一个obj的mesh对象中的数据，加快导出速度。
    '''
    
    def __init__(self,mesh:bpy.types.Mesh) -> None:
        self.mesh = mesh

    '''
    # 下面这里是获取BLENDWEIGHTS和BLENDINDICES的代码，但是只支持前四个BLENDWEIGHTS和BLENDINDICES
    # 我们需要扩展让它支持任意多个，并且每四个为一组
    # 比如BLENDWEIGHTS R8G8B8A8_UNORM  BLENDWEIGHTS1 R8G8B8A8_UNORM  
    # 也会有对应的BLENDINDICES和BLENDINDICES1，数据类型为R8G8B8A8_UINT等等
    # 数据类型是后面决定的，但是我们这里要提前准备好BLENDWEIGHTS和BLENDINDICES的内容，反正肯定不是4个
    # 创建一个包含所有循环顶点索引的NumPy数组

    这个V1要留着参考，V3目前正在使用，但是后续仍然有可能有更新的版本。
    '''
    def get_blendweights_blendindices_v1(self,normalize_weights:bool = False):

        mesh_loops = self.mesh.loops
        mesh_loops_length = len(mesh_loops)
        mesh_vertices = self.mesh.vertices

        loop_vertex_indices = numpy.empty(mesh_loops_length, dtype=int)
        mesh_loops.foreach_get("vertex_index", loop_vertex_indices)

        max_groups = 4

        # Extract and sort the top 4 groups by weight for each vertex.
        sorted_groups = [
            sorted(v.groups, key=lambda x: x.weight, reverse=True)[:max_groups]
            for v in mesh_vertices
        ]

        # Initialize arrays to hold all groups and weights with zeros.
        all_groups = numpy.zeros((len(mesh_vertices), max_groups), dtype=int)
        all_weights = numpy.zeros((len(mesh_vertices), max_groups), dtype=numpy.float32)


        # Fill the pre-allocated arrays with group indices and weights.
        for v_index, groups in enumerate(sorted_groups):
            num_groups = min(len(groups), max_groups)
            all_groups[v_index, :num_groups] = [g.group for g in groups][:num_groups]
            all_weights[v_index, :num_groups] = [g.weight for g in groups][:num_groups]

        # Initialize the blendindices and blendweights with zeros.
        blendindices = numpy.zeros((mesh_loops_length, max_groups), dtype=numpy.uint32)
        blendweights = numpy.zeros((mesh_loops_length, max_groups), dtype=numpy.float32)

        # Map from loop_vertex_indices to precomputed data using advanced indexing.
        valid_mask = (0 <= numpy.array(loop_vertex_indices)) & (numpy.array(loop_vertex_indices) < len(mesh_vertices))
        valid_indices = loop_vertex_indices[valid_mask]

        blendindices[valid_mask] = all_groups[valid_indices]
        blendweights[valid_mask] = all_weights[valid_indices]

        # XXX 必须对当前obj对象执行权重规格化，否则模型细分后会导致模型坑坑洼洼
        
        blendweights = blendweights / numpy.sum(blendweights, axis=1)[:, None]

        blendweights_dict = {}
        blendindices_dict = {}

        blendweights_dict[0] = blendweights
        blendindices_dict[0] = blendindices
        return blendweights_dict, blendindices_dict
    

    def get_blendweights_blendindices_v3(self, normalize_weights: bool = False):
        print("get_blendweights_blendindices_v3")
        print(normalize_weights)

        mesh_loops = self.mesh.loops
        mesh_loops_length = len(mesh_loops)
        mesh_vertices = self.mesh.vertices
        
        # 获取循环顶点的顶点索引
        loop_vertex_indices = numpy.empty(mesh_loops_length, dtype=int)
        mesh_loops.foreach_get("vertex_index", loop_vertex_indices)
        
        # 计算每个顶点的最大组数（向上取整到最近的4的倍数）
        max_groups_per_vertex = 0
        for v in mesh_vertices:
            group_count = len(v.groups)
            if group_count > max_groups_per_vertex:
                max_groups_per_vertex = group_count
        
        # 将最大组数对齐到4的倍数（每个语义索引包含4个权重）
        max_groups_per_vertex = ((max_groups_per_vertex + 3) // 4) * 4
        num_sets = max_groups_per_vertex // 4  # 需要的语义索引数量

        # print("num_sets: " + str(num_sets))
        
        # 如果最大组数小于4，至少需要1组
        if num_sets == 0 and max_groups_per_vertex > 0:
            num_sets = 1
        
        groups_per_set = 4
        total_groups = num_sets * groups_per_set

        # 提取并排序顶点组（取前 total_groups 个）
        sorted_groups = [
            sorted(v.groups, key=lambda x: x.weight, reverse=True)[:total_groups]
            for v in mesh_vertices
        ]

        # 初始化存储数组
        all_groups = numpy.zeros((len(mesh_vertices), total_groups), dtype=int)
        all_weights = numpy.zeros((len(mesh_vertices), total_groups), dtype=numpy.float32)

        # 填充权重和索引数据
        for v_idx, groups in enumerate(sorted_groups):
            count = min(len(groups), total_groups)
            all_groups[v_idx, :count] = [g.group for g in groups][:count]
            all_weights[v_idx, :count] = [g.weight for g in groups][:count]

        # 关键步骤：整体归一化所有权重
        if normalize_weights:
            # 计算每个顶点的权重总和
            weight_sums = numpy.sum(all_weights, axis=1)
            # 避免除以零（将总和为0的顶点设置为1，这样权重保持为0）
            weight_sums[weight_sums == 0] = 1
            # 归一化权重
            all_weights = all_weights / weight_sums[:, numpy.newaxis]


        # 将数据重塑为 [顶点数, 组数, 4]
        all_weights_reshaped = all_weights.reshape(len(mesh_vertices), num_sets, groups_per_set)
        all_groups_reshaped = all_groups.reshape(len(mesh_vertices), num_sets, groups_per_set)

        # 初始化输出字典
        blendweights_dict = {}
        blendindices_dict = {}


        # 为每组数据创建独立数组
        for set_idx in range(num_sets):
            # 初始化当前组的存储
            blendweights = numpy.zeros((mesh_loops_length, groups_per_set), dtype=numpy.float32)
            blendindices = numpy.zeros((mesh_loops_length, groups_per_set), dtype=numpy.uint32)
            
            # 创建有效索引掩码
            valid_mask = (0 <= loop_vertex_indices) & (loop_vertex_indices < len(mesh_vertices))
            valid_indices = loop_vertex_indices[valid_mask]
            
            # 映射数据到循环顶点
            blendweights[valid_mask] = all_weights_reshaped[valid_indices, set_idx, :]
            blendindices[valid_mask] = all_groups_reshaped[valid_indices, set_idx, :]

            
            # 3. 关键：再把每行 4 个权重重新归一化到 1（和 v1 最后一行等价）
            if normalize_weights:
                row_sum = numpy.sum(blendweights, axis=1, keepdims=True)
                # 避免 0 除
                numpy.putmask(row_sum, row_sum == 0, 1.0)
                blendweights = blendweights / row_sum

            
            # 存储到字典（使用SemanticIndex作为键）
            blendweights_dict[set_idx] = blendweights
            blendindices_dict[set_idx] = blendindices

        # blendweights = blendweights / numpy.sum(blendweights, axis=1)[:, None]
        # print("blendweights_dict: " + str(blendweights_dict[2][0]))
        # print("blendindices_dict: " + str(blendindices_dict[2][0]))

        return blendweights_dict, blendindices_dict
    
