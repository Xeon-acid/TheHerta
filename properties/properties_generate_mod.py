import bpy


class Properties_GenerateMod(bpy.types.PropertyGroup):
    open_mod_folder_after_generate_mod: bpy.props.BoolProperty(
        name="生成后打开Mod文件夹",
        description="勾选后，在生成Mod完成后自动打开Mod文件夹",
        default=True
    ) # type: ignore
    
    @classmethod
    def open_mod_folder_after_generate_mod(cls):
        '''
        bpy.context.scene.properties_generate_mod.open_mod_folder_after_generate_mod
        '''
        return bpy.context.scene.properties_generate_mod.open_mod_folder_after_generate_mod

    zzz_use_slot_fix: bpy.props.BoolProperty(
        name="槽位风格贴图使用SlotFix技术",
        description="仅适用于槽位风格贴图，勾选后，特定名称标记的贴图将使用SlotFix风格，能一定程度上解决槽位风格贴图跨槽位的问题，跨Pixel槽位指的是在前一个DrawCall中是ps-t3但是下一个DrawCall变为ps-t5这种情况，但由于负责维护的人也在偷懒所以并不可靠",
        default=False
    ) # type: ignore


    @classmethod
    def zzz_use_slot_fix(cls):
        '''
        bpy.context.scene.properties_generate_mod.zzz_use_slot_fix
        '''
        return bpy.context.scene.properties_generate_mod.zzz_use_slot_fix
    
    forbid_auto_texture_ini: bpy.props.BoolProperty(
        name="禁止自动贴图流程",
        description="生成Mod时禁止生成贴图相关ini部分",
        default=False
    ) # type: ignore


    @classmethod
    def forbid_auto_texture_ini(cls):
        '''
        bpy.context.scene.properties_generate_mod.forbid_auto_texture_ini
        '''
        return bpy.context.scene.properties_generate_mod.forbid_auto_texture_ini
    
    generate_branch_mod_gui: bpy.props.BoolProperty(
        name="生成分支切换Mod面板(测试版)",
        description="生成Mod时，生成一个基于当前集合架构的分支Mod面板，可在游戏中按住Ctrl + Alt呼出，仍在测试改进中",
        default=False
    ) # type: ignore


    @classmethod
    def generate_branch_mod_gui(cls):
        '''
        bpy.context.scene.properties_generate_mod.generate_branch_mod_gui
        '''
        return bpy.context.scene.properties_generate_mod.generate_branch_mod_gui
    

    recalculate_tangent: bpy.props.BoolProperty(
        name="向量归一化法线存入TANGENT(全局)",
        description="使用向量相加归一化重计算所有模型的TANGENT值，勾选此项后无法精细控制具体某个模型是否计算，是偷懒选项,在不勾选时默认使用右键菜单中标记的选项。\n" \
        "用途:\n" \
        "1.一般用于修复GI角色,HI3 1.0角色,HSR角色轮廓线。\n" \
        "2.用于修复模型由于TANGENT不正确导致的黑色色块儿问题，比如HSR的薄裙子可能会出现此问题。",
        default=False
    ) # type: ignore

    recalculate_color: bpy.props.BoolProperty(
        name="算术平均归一化法线存入COLOR(全局)",
        description="使用算术平均归一化重计算所有模型的COLOR值，勾选此项后无法精细控制具体某个模型是否计算，是偷懒选项,在不勾选时默认使用右键菜单中标记的选项，仅用于HI3 2.0角色修复轮廓线",
        default=False
    ) # type: ignore

    position_override_filter_draw_type :bpy.props.BoolProperty(
        name="Position替换添加DRAW_TYPE = 1判断",
        description="在NPC与VAT-PreSKinning的NPC冲突时会用到此技术，例如HSR匹诺康尼NPC\n格式：\nif DRAW_TYPE == 1\n  ........\nendif",
        default=False
    ) # type: ignore

    vertex_limit_raise_add_filter_index:bpy.props.BoolProperty(
        name="VertexLimitRaise添加filter_index过滤器",
        description="在NPC与VAT-PreSKinning的NPC冲突时会用到此技术，例如HSR匹诺康尼NPC\n格式:\nfilter_index = 3000\n\n....\n\nif vb0 == 3000\n  ........\nendif",
        default=False
    ) # type: ignore


    slot_style_texture_add_filter_index:bpy.props.BoolProperty(
        name="槽位风格贴图添加filter_index过滤器",
        description="可解决HSR知更鸟多层渲染问题，可解决ZZZ NPC贴图俯视仰视槽位不一致问题（生成的只是模板，仍需手动添加或更改槽位以适配具体情况）",
        default=False
    ) # type: ignore

    only_use_marked_texture:bpy.props.BoolProperty(
        name="只使用标记过的贴图",
        description="勾选后不会再生成Hash风格的RenderTextures里的自动贴图，而是完全使用用户标记过的贴图，如果用户遗漏了标记，则不会生成对应没标记过的贴图的ini内容",
        default=False
    ) # type: ignore

    
    # only_use_marked_texture
    @classmethod
    def only_use_marked_texture(cls):
        '''
        bpy.context.scene.properties_generate_mod.only_use_marked_texture
        '''
        return bpy.context.scene.properties_generate_mod.only_use_marked_texture
    



    
    @classmethod
    def author_name(cls):
        '''
        bpy.context.scene.properties_generate_mod.credit_info_author_name
        '''
        return bpy.context.scene.properties_generate_mod.credit_info_author_name
    
    @classmethod
    def author_link(cls):
        '''
        bpy.context.scene.properties_generate_mod.credit_info_author_social_link
        '''
        return bpy.context.scene.properties_generate_mod.credit_info_author_social_link
    
    @classmethod
    def recalculate_tangent(cls):
        '''
        bpy.context.scene.properties_generate_mod.recalculate_tangent
        '''
        return bpy.context.scene.properties_generate_mod.recalculate_tangent
    
    @classmethod
    def recalculate_color(cls):
        '''
        bpy.context.scene.properties_generate_mod.recalculate_color
        '''
        return bpy.context.scene.properties_generate_mod.recalculate_color
    

    @classmethod
    def position_override_filter_draw_type(cls):
        '''
        bpy.context.scene.properties_generate_mod.position_override_filter_draw_type
        '''
        return bpy.context.scene.properties_generate_mod.position_override_filter_draw_type
    
    @classmethod
    def vertex_limit_raise_add_filter_index(cls):
        '''
        bpy.context.scene.properties_generate_mod.vertex_limit_raise_add_filter_index
        '''
        return bpy.context.scene.properties_generate_mod.vertex_limit_raise_add_filter_index

    @classmethod
    def slot_style_texture_add_filter_index(cls):
        '''
        bpy.context.scene.properties_generate_mod.slot_style_texture_add_filter_index
        '''
        return bpy.context.scene.properties_generate_mod.slot_style_texture_add_filter_index
    

    
    