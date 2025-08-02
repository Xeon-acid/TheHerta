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





