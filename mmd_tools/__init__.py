# -*- coding: utf-8 -*-

bl_info = {
    "name": "mmd_tools",
    "author": "sugiany",
    "version": (0, 7, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Tool Shelf > MMD Tools Panel",
    "description": "Utility tools for MMD model editing. (powroupi's forked version)",
    "warning": "",
    "wiki_url": "https://github.com/powroupi/blender_mmd_tools/wiki",
    "tracker_url": "https://github.com/powroupi/blender_mmd_tools/issues",
    "category": "Object",
    }

__bl_classes = []
def register_wrap(cls):
    #print('%3d'%len(__bl_classes), cls)
    #assert(cls not in __bl_classes)
    if hasattr(cls, 'bl_rna'):
        __bl_classes.append(cls)
    return cls

if "bpy" in locals():
    if bpy.app.version < (2, 71, 0):
        import imp as importlib
    else:
        import importlib
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
else:
    import os
    import bpy
    import logging
    from bpy.types import AddonPreferences
    from bpy.props import StringProperty
    from bpy.app.handlers import persistent

    from . import properties
    from . import operators
    from . import panels

if bpy.app.version < (2, 80, 0):
    bl_info['blender'] = (2, 70, 0)

logging.basicConfig(format='%(message)s', level=logging.DEBUG)


@register_wrap
class MMDToolsAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    shared_toon_folder = StringProperty(
            name="Shared Toon Texture Folder",
            description=('Directory path to toon textures. This is normally the ' +
                         '"Data" directory within of your MikuMikuDance directory'),
            default=os.path.dirname(os.path.abspath(__file__)) + os.path.sep + "textures",
            subtype='DIR_PATH',
            )
    base_texture_folder = StringProperty(
            name='Base Texture Folder',
            description=('This directory path will be used to determine the relative ' +
                         'path of the textures you use'),
            subtype='DIR_PATH'
            )
    dictionary_folder = StringProperty(
            name='Dictionary Folder',
            description='Path for searching csv dictionaries',
            subtype='DIR_PATH',
            default=__file__[:-11],
            )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "shared_toon_folder")
        layout.prop(self, "base_texture_folder")
        layout.prop(self, "dictionary_folder")


def menu_func_import(self, context):
    self.layout.operator(operators.fileio.ImportPmx.bl_idname, text='MikuMikuDance Model (.pmd, .pmx)', icon='OUTLINER_OB_ARMATURE')
    self.layout.operator(operators.fileio.ImportVmd.bl_idname, text='MikuMikuDance Motion (.vmd)', icon='ANIM')
    self.layout.operator(operators.fileio.ImportVpd.bl_idname, text='Vocaloid Pose Data (.vpd)', icon='POSE_HLT')

def menu_func_export(self, context):
    self.layout.operator(operators.fileio.ExportPmx.bl_idname, text='MikuMikuDance Model (.pmx)', icon='OUTLINER_OB_ARMATURE')
    self.layout.operator(operators.fileio.ExportVmd.bl_idname, text='MikuMikuDance Motion (.vmd)', icon='ANIM')
    self.layout.operator(operators.fileio.ExportVpd.bl_idname, text='Vocaloid Pose Data (.vpd)', icon='POSE_HLT')

def menu_func_armature(self, context):
    self.layout.operator(operators.model.CreateMMDModelRoot.bl_idname, text='Create MMD Model', icon='OUTLINER_OB_ARMATURE')

@persistent
def load_handler(dummy):
    from mmd_tools.core.sdef import FnSDEF
    FnSDEF.clear_cache()
    FnSDEF.register_driver_function()

def register():
    for cls in __bl_classes:
        bpy.utils.register_class(cls)
    print(__name__, 'registed %d classes'%len(__bl_classes))
    properties.register()
    bpy.app.handlers.load_post.append(load_handler)
    if bpy.app.version < (2, 80, 0):
        bpy.types.INFO_MT_file_import.append(menu_func_import)
        bpy.types.INFO_MT_file_export.append(menu_func_export)
        bpy.types.INFO_MT_armature_add.append(menu_func_armature)
    else:
        bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
        bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
        bpy.types.VIEW3D_MT_armature_add.append(menu_func_armature)

def unregister():
    if bpy.app.version < (2, 80, 0):
        bpy.types.INFO_MT_file_import.remove(menu_func_import)
        bpy.types.INFO_MT_file_export.remove(menu_func_export)
        bpy.types.INFO_MT_armature_add.remove(menu_func_armature)
    else:
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
        bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
        bpy.types.VIEW3D_MT_armature_add.remove(menu_func_armature)
    bpy.app.handlers.load_post.remove(load_handler)
    properties.unregister()
    for cls in reversed(__bl_classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
