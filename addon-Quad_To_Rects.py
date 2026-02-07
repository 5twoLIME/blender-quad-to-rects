#Quad_To_Rects add-on for Blender 5.0
#Please visit @5twoLIME on X for more details
#This add-on is made with the help of Claude. Please feel free to improve this script:)

bl_info = {
    "name": "Quad to Rects",
    "author": "5twoLIME",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "UV Editor > Sidebar > Quad to Rects",
    "description": "Rectangularize selected quad and apply Follow Active Quads to entire mesh",
    "category": "UV",
}

import bpy
import bmesh

class UVQUAD_OT_rectangularize(bpy.types.Operator):
    """Rectangularize selected quad UV and apply Follow Active Quads"""
    bl_idname = "uv.quad_to_rects"
    bl_label = "Quad to Rects"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'
    
    def execute(self, context):
        print("=== STARTING QUAD TO RECTS ===")
        
        # Get all selected objects in edit mode
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        print(f"Selected mesh objects: {len(selected_objects)}")
        
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected!")
            return {'CANCELLED'}
        
        # Find which object has a selected face
        target_obj = None
        target_face = None
        
        for obj in selected_objects:
            if obj.mode != 'EDIT':
                continue
                
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            
            # Check if this object has any selected faces
            selected_faces = [f for f in bm.faces if f.select]
            
            if selected_faces:
                print(f"Found selected face in object: {obj.name}")
                target_obj = obj
                target_face = selected_faces[0]
                break
        
        if not target_obj or not target_face:
            self.report({'ERROR'}, "No face selected in any object!")
            return {'CANCELLED'}
        
        print(f"Working on object: {target_obj.name}")
        
        obj = target_obj
        face = target_face
        
        me = obj.data
        print(f"Mesh: {me.name}")
        
        bm = bmesh.from_edit_mesh(me)
        print(f"BMesh created with {len(bm.faces)} faces")
        
        uv_layer = bm.loops.layers.uv.active
        
        if not uv_layer:
            self.report({'ERROR'}, "No UV layer found!")
            return {'CANCELLED'}
        
        print(f"UV layer found: {uv_layer}")
        
        # Work in UV editor mode - turn ON sync and use face select
        context.scene.tool_settings.use_uv_select_sync = True
        context.scene.tool_settings.mesh_select_mode = (False, False, True)  # Face mode
        
        if len(face.loops) != 4:
            self.report({'ERROR'}, "Selected face is not a quad!")
            return {'CANCELLED'}
        
        print(f"Processing quad with {len(face.loops)} vertices")
        
        # Get the 4 loops of the quad
        loops = list(face.loops)
        
        # Get UV coordinates
        uvs = [loop[uv_layer].uv for loop in loops]
        
        print(f"Original UVs: {[(round(uv.x, 3), round(uv.y, 3)) for uv in uvs]}")
        
        # Find the bounding box of the quad
        u_coords = [uv.x for uv in uvs]
        v_coords = [uv.y for uv in uvs]
        
        min_u = min(u_coords)
        max_u = max(u_coords)
        min_v = min(v_coords)
        max_v = max(v_coords)
        
        print(f"Bounds - U: [{round(min_u, 3)}, {round(max_u, 3)}], V: [{round(min_v, 3)}, {round(max_v, 3)}]")
        
        # For each loop, also update connected loops from neighboring faces
        for i, loop in enumerate(loops):
            uv = uvs[i]
            
            # Determine target position
            target_x = min_u if uv.x < (min_u + max_u) / 2 else max_u
            target_y = min_v if uv.y < (min_v + max_v) / 2 else max_v
            
            # Update this loop's UV
            uv.x = target_x
            uv.y = target_y
            
            # Find all loops that share this vertex and update their UVs too
            vert = loop.vert
            for other_face in vert.link_faces:
                for other_loop in other_face.loops:
                    if other_loop.vert == vert:
                        # Check if this UV is at the same position (shared)
                        other_uv = other_loop[uv_layer].uv
                        # Only update if very close to original position (within 0.001)
                        if abs(other_uv.x - uvs[i].x) < 0.001 and abs(other_uv.y - uvs[i].y) < 0.001:
                            other_uv.x = target_x
                            other_uv.y = target_y
        
        print(f"Rectangularized UVs: {[(round(uv.x, 3), round(uv.y, 3)) for uv in uvs]}")
        
        # Update the mesh
        bmesh.update_edit_mesh(me)
        
        print("Done! Quad is now a perfect rectangle with connected edges")
        
        # Now run Follow Active Quads on the entire island
        print("Running Follow Active Quads on island...")
        
        # Turn off UV sync so we can work in UV space
        original_sync = context.scene.tool_settings.use_uv_select_sync
        print(f"Original UV sync: {original_sync}")
        context.scene.tool_settings.use_uv_select_sync = False
        
        # Select all faces in the mesh first
        for f in bm.faces:
            f.select = True
        
        bmesh.update_edit_mesh(me)
        
        # Now select all UVs
        bpy.ops.uv.select_all(action='SELECT')
        
        # Set the rectangularized face as active
        bm.faces.active = face
        bmesh.update_edit_mesh(me)
        
        print(f"Active face set, all UVs selected")
        
        # Run Follow Active Quads
        print("Running Follow Active Quads...")
        result = bpy.ops.uv.follow_active_quads()
        print(f"Follow Active Quads result: {result}")
        
        # Restore UV sync
        context.scene.tool_settings.use_uv_select_sync = original_sync
        
        self.report({'INFO'}, "Quad rectangularized and Follow Active Quads applied!")
        print("Complete! Entire mesh is now rectangularized")
        
        return {'FINISHED'}


class UVQUAD_PT_panel(bpy.types.Panel):
    """Creates a Panel in the UV Editor sidebar"""
    bl_label = "Quad to Rects"
    bl_idname = "UVQUAD_PT_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Quad to Rects"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.scale_y = 2.0
        row.operator("uv.quad_to_rects", text="Quad to Rects", icon='CHECKBOX_DEHLT')


def register():
    bpy.utils.register_class(UVQUAD_OT_rectangularize)
    bpy.utils.register_class(UVQUAD_PT_panel)


def unregister():
    bpy.utils.unregister_class(UVQUAD_PT_panel)
    bpy.utils.unregister_class(UVQUAD_OT_rectangularize)


if __name__ == "__main__":
    register()
