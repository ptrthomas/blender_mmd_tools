# -*- coding: utf-8 -*-

from bpy.props import FloatProperty
from bpy.types import Operator

from mmd_tools.core.lamp import MMDLamp

class ConvertToMMDLamp(Operator):
    bl_idname = 'mmd_tools.convert_to_mmd_lamp'
    bl_label = 'Convert to MMD Lamp'
    bl_description = 'Create a lamp rig for MMD'

    scale = FloatProperty(
        name='Scale',
        description='Scaling factor for initializing the lamp',
        default=1.0,
        )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'LAMP'

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)

    def execute(self, context):
        MMDLamp.convertToMMDLamp(context.active_object, self.scale)
        return {'FINISHED'}
