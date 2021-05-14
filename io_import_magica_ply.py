bl_info = {
    "name": "Import Magica Voxel .ply",
    "author": "mantrivo",
    "version": (0, 9, 1),
    "blender": (2, 80, 0),
    "location": "File > Import",
    "description": "Imports a .ply File form Magica Voxel, generates a Texture and optimizes Geometry",
    "category": "Import-Export",
    "tracker_url": "https://github.com/mantrivo/import_magica_voxel_ply/issues",
    "warning": "Packing UV Islands for complex geometry might not work. Requires ply and Images as Planes addon."
}


import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper
import os
from io_mesh_ply import import_ply


def ensure_mat(color, color_hex):
    D=bpy.data
    matrial_id =D.materials.find(color_hex)
    if matrial_id == -1:
        mat=D.materials.new(color_hex)
        mat.diffuse_color=color
    else:
        mat=D.materials[matrial_id]
    return mat

def clean_node_tree(node_tree):
    """Clear all nodes in a shader node tree except the output.

    Returns the output node
    """
    nodes = node_tree.nodes
    for node in list(nodes):  # copy to avoid altering the loop's data source
        if not node.type == 'OUTPUT_MATERIAL':
            nodes.remove(node)

    return node_tree.nodes[0]

def get_bake_material(name):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    node_tree = material.node_tree
    out_node = clean_node_tree(node_tree)
    out_node.select = False

    diffuse_shader = node_tree.nodes.new('ShaderNodeBsdfDiffuse')
    diffuse_shader.select = False
    node_tree.links.new(out_node.inputs['Surface'], diffuse_shader.outputs[0])

    mix_rgb = node_tree.nodes.new('ShaderNodeMixRGB')
    mix_rgb.inputs[0].default_value = 0.0
    mix_rgb.select = False
    node_tree.links.new(diffuse_shader.inputs['Color'], mix_rgb.outputs['Color'])
    
    vertex_color = node_tree.nodes.new('ShaderNodeVertexColor')
    vertex_color.select = False
    node_tree.links.new(mix_rgb.inputs['Color1'], vertex_color.outputs['Color'])
    #bpy.ops.node.add_node(type="ShaderNodeVertexColor", use_transform=True)

    
    texture = node_tree.nodes.new('ShaderNodeTexImage')
    texture.interpolation = 'Closest'
    texture.select = True
    node_tree.links.new(mix_rgb.inputs['Color2'], texture.outputs['Color'])

    try:
        from io_import_images_as_planes import auto_align_nodes
        auto_align_nodes(node_tree)
    except:
        pass

    return material

def get_texture_node(node_tree):
    nodes = node_tree.nodes
    result = None
    for node in nodes:
        node.select = (node.type == 'TEX_IMAGE')
        if node.type == 'TEX_IMAGE':
            result = node

    return result


class IMPORT_MAGICA_PLY_OT(Operator, ImportHelper):
    """Create a new Mesh Object"""
    bl_idname = "import_mesh.magica_ply"
    bl_label = "Import Magica Voxel .ply"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".ply"
    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    files: CollectionProperty(
        name="File Path",
        description="File path used for importing the PLY file",
        type=bpy.types.OperatorFileListElement,
    )

    directory: StringProperty()

    use_modifieres: BoolProperty(default=True, name="Use Modifiers")

    use_save_texture: BoolProperty(default=False, name="Save Textures")
    

    def import_magica_ply(self, context, filename, filepath):
        if context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        import_ply.load(self, context, filename)
        
        obj = context.active_object
        mesh = obj.data
        col = mesh.vertex_colors[0].data
        colors = []
        colors_hex = []
        matrials_index = []
        
        
        material = get_bake_material(obj.name)
        if len(obj.material_slots) == 0:
            mesh.materials.append(material)
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        print("remove_doubles")
        bpy.ops.mesh.remove_doubles()
        print("uv.cube_project")
        #bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.0,
        #            area_weight=0.0, correct_aspect=True)
        bpy.ops.uv.cube_project(cube_size=0.1, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=False)
        print("uv.pack_islands")
        bpy.ops.uv.pack_islands(rotate=False, margin=0)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        print("get dimensions")
        uv = mesh.uv_layers[0].data
        u_min=1.0
        for point in uv:
            if point.uv[0] > 0.00001 and point.uv[0] < u_min:
                u_min = point.uv[0]

        width = round(1/u_min)
        print(f"Image width:  {width} first uv.u: {u_min}")
        v_min=1.0
        for point in uv:
            if point.uv[1] > 0.00001 and point.uv[1] < v_min:
                v_min = point.uv[1]

        height = round(1/v_min)
        print(f"Image height: {height} first uv.v: {v_min}")
        img = bpy.data.images.new(obj.name + '_diffuse', width=width, height=height)
        texture_node = get_texture_node(material.node_tree)
        texture_node.image = img

        context.scene.render.engine = "CYCLES"
        imagefilepath = os.path.join(filepath, obj.name + "_diffuse.png")
        img.filepath = imagefilepath
        print("bake vertex color to image")
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'},
                    filepath=imagefilepath, save_mode='EXTERNAL',
                    width=width, height=width, margin=0,
                    use_selected_to_active=False, max_ray_distance=0.2,
                    cage_extrusion=0.2, normal_space='TANGENT',
                    target='IMAGE_TEXTURES', use_clear=True,
                    use_cage=True, use_split_materials=False,
                    use_automatic_name=False)
        if self.use_modifieres:
            print("adding Modifiers")
            decimate = obj.modifiers.new('Decimate', 'DECIMATE')
            decimate.decimate_type = "DISSOLVE"
            decimate.delimit = {'UV'}
            
            decimate = obj.modifiers.new('Triangulate', 'TRIANGULATE')
        else:
            bpy.ops.object.mode_set(mode='EDIT')
            print("mesh.dissolve_limited")
            bpy.ops.mesh.dissolve_limited(delimit={'UV'})
            print("mesh.vert_connect_concave")
            bpy.ops.mesh.vert_connect_concave()
            print("mesh.quads_convert_to_tris")
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

        if self.use_save_texture:
            print("saving Texture: " + imagefilepath)
            img.save()
        print("done")
        bpy.ops.object.mode_set(mode='OBJECT')

    def execute(self, context):

        context.window.cursor_set('WAIT')

        paths = [
            os.path.join(self.directory, name.name)
            for name in self.files
        ]

        if not paths:
            paths.append(self.filepath)

        for path in paths:
            self.import_magica_ply(context, path, self.directory)

        context.window.cursor_set('DEFAULT')
        return {'FINISHED'}


# Registration

def add_object_button(self, context):
    self.layout.operator(
        IMPORT_MAGICA_PLY_OT.bl_idname)

def register():
    bpy.utils.register_class(IMPORT_MAGICA_PLY_OT)
    bpy.types.TOPBAR_MT_file_import.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(IMPORT_MAGICA_PLY_OT)
    bpy.types.TOPBAR_MT_file_import.remove(add_object_button)


if __name__ == "__main__":
    register()
