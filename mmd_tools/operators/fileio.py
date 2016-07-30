# -*- coding: utf-8 -*-

import logging
import re
import traceback
import os

import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper

from mmd_tools import auto_scene_setup
from mmd_tools.utils import selectAObject
from mmd_tools.utils import makePmxBoneMap

import mmd_tools.core.pmd.importer as pmd_importer
import mmd_tools.core.pmx.importer as pmx_importer
import mmd_tools.core.pmx.exporter as pmx_exporter
import mmd_tools.core.vmd.importer as vmd_importer
import mmd_tools.core.model as mmd_model



LOG_LEVEL_ITEMS = [
    ('DEBUG', '4. DEBUG', '', 1),
    ('INFO', '3. INFO', '', 2),
    ('WARNING', '2. WARNING', '', 3),
    ('ERROR', '1. ERROR', '', 4),
    ]

def log_handler(log_level, filepath=None):
    if filepath is None:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(filepath, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    return handler


def _update_types(cls, prop):
    types = cls.types.copy()

    if 'PHYSICS' in types:
        types.add('ARMATURE')
    if 'DISPLAY' in types:
        types.add('ARMATURE')
    if 'MORPHS' in types:
        types.add('ARMATURE')
        types.add('MESH')

    if types != cls.types:
        cls.types = types # trigger update


class ImportPmx(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_model'
    bl_label = 'Import Model file (.pmd, .pmx)'
    bl_description = 'Import a Model file (.pmd, .pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx;*.pmd', options={'HIDDEN'})

    types = bpy.props.EnumProperty(
        name='Types',
        description='Select which parts will be imported',
        options={'ENUM_FLAG'},
        items = [
            ('MESH', 'Mesh', 'Mesh', 1),
            ('ARMATURE', 'Armature', 'Armature', 2),
            ('PHYSICS', 'Physics', 'Rigidbodies and joints (include Armature)', 4),
            ('DISPLAY', 'Display', 'Display frames (include Armature)', 8),
            ('MORPHS', 'Morphs', 'Morphs (include Armature and Mesh)', 16),
            ],
        default={'MESH', 'ARMATURE', 'PHYSICS', 'DISPLAY', 'MORPHS',},
        update=_update_types,
        )
    scale = bpy.props.FloatProperty(
        name='Scale',
        description='Scaling factor for importing the model',
        default=0.2,
        )
    renameBones = bpy.props.BoolProperty(
        name='Rename bones',
        description='Rename the bones to be more blender suitable',
        default=True,
        )
    use_mipmap = bpy.props.BoolProperty(
        name='use MIP maps for UV textures',
        description='Specify if mipmaps will be generated',
        default=True,
        )
    sph_blend_factor = bpy.props.FloatProperty(
        name='influence of .sph textures',
        description='The diffuse color factor of texture slot for .sph textures',
        default=1.0,
        )
    spa_blend_factor = bpy.props.FloatProperty(
        name='influence of .spa textures',
        description='The diffuse color factor of texture slot for .spa textures',
        default=1.0,
        )
    log_level = bpy.props.EnumProperty(
        name='Log level',
        description='Select log level',
        items=LOG_LEVEL_ITEMS,
        default='DEBUG',
        )
    save_log = bpy.props.BoolProperty(
        name='Create a log file',
        description='Create a log file',
        default=False,
        )

    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.import.log')
            logger.addHandler(handler)
        try:
            importer_cls = pmx_importer.PMXImporter
            if re.search('\.pmd$', self.filepath, flags=re.I):
                importer_cls = pmd_importer.PMDImporter

            importer_cls().execute(
                filepath=self.filepath,
                types=self.types,
                scale=self.scale,
                rename_LR_bones=self.renameBones,
                use_mipmap=self.use_mipmap,
                sph_blend_factor=self.sph_blend_factor,
                spa_blend_factor=self.spa_blend_factor,
                )
        except Exception as e:
            err_msg = traceback.format_exc()
            logging.error(err_msg)
            self.report({'ERROR'}, err_msg)
        finally:
            if self.save_log:
                logger.removeHandler(handler)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportVmd(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_vmd'
    bl_label = 'Import VMD file (.vmd)'
    bl_description = 'Import a VMD file (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(
        name='Scale',
        description='Scaling factor for importing the motion',
        default=0.2,
        )
    margin = bpy.props.IntProperty(
        name='Margin',
        description='How many frames added before motion starting',
        min=0,
        default=0,
        )
    bone_mapper = bpy.props.EnumProperty(
        name='Bone Mapper',
        description='Select bone mapper',
        items=[
            ('BLENDER', 'Blender', 'Use blender bone name', 0),
            ('PMX', 'PMX', 'Use japanese name of MMD bone', 1),
            ('RENAMED_BONES', 'Renamed bones', 'Rename the bone of motion data to be blender suitable', 2),
            ],
        default='PMX',
        )
    update_scene_settings = bpy.props.BoolProperty(
        name='Update scene settings',
        description='Update frame range and frame rate (30 fps)',
        default=True,
        )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        active_object = context.active_object
        hidden_obj = []
        for i in context.selected_objects:
            root = mmd_model.Model.findRoot(i)
            if root == i:
                rig = mmd_model.Model(root)
                arm = rig.armature()
                if arm.hide:
                    arm.hide = False
                    hidden_obj.append(arm)
                arm.select = True
                for m in rig.meshes():
                    if m.hide:
                        m.hide = False
                        hidden_obj.append(m)
                    m.select = True

        bone_mapper = None
        if self.bone_mapper == 'PMX':
            bone_mapper = makePmxBoneMap
        elif self.bone_mapper == 'RENAMED_BONES':
            bone_mapper = vmd_importer.RenamedBoneMapper

        importer = vmd_importer.VMDImporter(
            filepath=self.filepath,
            scale=self.scale,
            bone_mapper=bone_mapper,
            frame_margin=self.margin,
            )

        for i in context.selected_objects:
            importer.assign(i)
        if self.update_scene_settings:
            auto_scene_setup.setupFrameRanges()
            auto_scene_setup.setupFps()

        for i in hidden_obj:
            i.select = False
            i.hide = True

        active_object.select = True
        context.scene.objects.active = active_object
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportPmx(Operator, ExportHelper):
    bl_idname = 'mmd_tools.export_pmx'
    bl_label = 'Export PMX file (.pmx)'
    bl_description = 'Export a PMX file (.pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx', options={'HIDDEN'})

    copy_textures = bpy.props.BoolProperty(
        name='Copy textures',
        description='Copy textures',
        default=True,
        )
    sort_materials = bpy.props.BoolProperty(
        name='Sort Materials',
        description=('Sort materials for alpha blending. '
                     'WARNING: Will not work if you have ' +
                     'transparent meshes inside the model. ' +
                     'E.g. blush meshes'),
        default=False,
        )

    log_level = bpy.props.EnumProperty(
        name='Log level',
        description='Select log level',
        items=LOG_LEVEL_ITEMS,
        default='DEBUG',
        )
    save_log = bpy.props.BoolProperty(
        name='Create a log file',
        description='Create a log file',
        default=False,
        )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and mmd_model.Model.findRoot(obj)

    def execute(self, context):
        active_object = context.active_object
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.export.log')
            logger.addHandler(handler)

        root = mmd_model.Model.findRoot(context.active_object)
        if root.mmd_root.editing_morphs > 0:
            # We have two options here: 
            # 1- report it to the user
            # 2- clear the active morphs (user will loose any changes to temp materials and UV) 
            bpy.ops.mmd_tools.clear_temp_materials()
            bpy.ops.mmd_tools.clear_uv_morph_view()        
            self.report({ 'WARNING' }, "Active editing morphs were cleared")
            # return { 'CANCELLED' }
        rig = mmd_model.Model(root)
        rig.clean()
        # Clear the pose before exporting
        if rig.armature():
            prev_show = root.mmd_root.show_armature
            root.mmd_root.show_armature = True
            selectAObject(rig.armature())
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.pose.transforms_clear()
            bpy.ops.object.mode_set(mode='OBJECT')
            root.mmd_root.show_armature = prev_show
        try:
            pmx_exporter.export(
                filepath=self.filepath,
                scale=root.mmd_root.scale,
                root=rig.rootObject(),
                armature=rig.armature(),
                meshes=rig.meshes(),
                rigid_bodies=rig.rigidBodies(),
                joints=rig.joints(),
                copy_textures=self.copy_textures,
                sort_materials=self.sort_materials,
                )
        except Exception as e:
            err_msg = traceback.format_exc()
            logging.error(err_msg)
            self.report({'ERROR'}, err_msg)
        finally:
            if self.save_log:
                logger.removeHandler(handler)

        active_object.select = True
        context.scene.objects.active = active_object
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
