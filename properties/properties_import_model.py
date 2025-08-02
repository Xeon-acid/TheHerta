import bpy

class Properties_ImportModel(bpy.types.PropertyGroup):
    model_scale: bpy.props.FloatProperty(
        name="模型导入大小比例",
        description="默认为1.0",
        default=1.0,
    ) # type: ignore

    @classmethod
    def model_scale(cls):
        '''
        bpy.context.scene.properties_import_model.model_scale
        '''
        return bpy.context.scene.properties_import_model.model_scale


    use_mirror_workflow: bpy.props.BoolProperty(
        name="使用非镜像工作流",
        description="默认为False, 启用后导入和导出模型将不再是镜像的，目前3Dmigoto的模型导入后是镜像存粹是由于历史遗留问题是错误的，但是当错误积累成粑粑山，人的习惯和旧的工程很难被改变，所以只有勾选后才能使用非镜像工作流",
        default=False,
    ) # type: ignore

    @classmethod
    def use_mirror_workflow(cls):
        '''
        bpy.context.scene.properties_import_model.use_mirror_workflow
        '''
        return bpy.context.scene.properties_import_model.use_mirror_workflow
