import bpy
import math
import bmesh
from mathutils import noise, Vector, Euler

bl_info = {
    "name": "Magic Fractal Tree",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Create a new Magic Fractal Tree",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

# Datastructure for tracking the complete tree
# This is necessary because the BMesh is freed and coverted to mesh data
# and this class helps facilitate later iteration through the tree's mesh
class MagicTreeNode:
    def __init__(self):
        self.parent_node = None
        self.node_branch = None
        self.child_nodes = []
        
    def __init__(self, pn, b):
        self.parent_node = pn
        self.node_branch = b
        self.child_nodes = []
        
    def set_parent(self, pn):
        self.parent_node = pn
    def set_branch(self, b):
        self.node_branch = b
    def set_child_node(self, cn):
        self.child_nodes.append(cn)    

# Get the indicies for each vertex in the branch
def indicies_from_branch(branch):
    indicies = []
    for vert in branch:
        indicies.append(vert.index)
    return indicies

# Vector.rotate() has the shortcomming of operating in world space
# To overcome this, the vector must first be shifted to global space, rotated,
# and then shifted back to local space
def rotate_local(eul, vec, local_vec):
    norm_vec = vec - local_vec
    
    norm_vec.rotate(eul)
    return norm_vec + local_vec

# Return a boolean whether or not to create a new branch
def should_create_branch(branch_split_prob):
    rand = noise.random()
    return rand < branch_split_prob

# Create a new branch on the passed-in BMesh, with count number of verticies, 
# a begin vertex, and a difference vertex. The vert_diff arg helps to ensure
# the correct distance is applied between each vertex (i.e. uniform edge len).
def create_branch(bm, count, random_bend_range, begin_vert, vert_diff):
    branch = []
    prev_vert = begin_vert
    i_range = range(count)

    for i in i_range:
        ext = bmesh.ops.extrude_vert_indiv(bm, verts=[prev_vert])

        new_verts = ext["verts"]
        # Extrude of a single vert only creates one new vertex
        curr_vert = new_verts[0]
        
        # First extend the new vert by the difference between the current
        # vert and the previous (NOTE: this vert may be before the branch
        # and is why it needs to be passed in as an argument.
        next_vert = Vector((prev_vert.co.x + vert_diff.x, 
                            prev_vert.co.y + vert_diff.y, 
                            prev_vert.co.z + vert_diff.z))
    
        # Randomize rotations on X then Y then Z axis. 
        # Randomness is constrained by an imput variable, expressed in degrees.
        shift = random_bend_range / 2
        rand_x = math.radians((noise.random() * random_bend_range) - shift)
        rand_y = math.radians((noise.random() * random_bend_range) - shift)
        rand_z = math.radians((noise.random() * random_bend_range) - shift)
    
        curr_vert.co = rotate_local(Euler((rand_x, rand_y, rand_z), 'XYZ'), next_vert, prev_vert.co)
        
        vert_diff = curr_vert.co - prev_vert.co        
        prev_vert = curr_vert
        branch.append(curr_vert)
    
    return branch

# Recursive function to create new branchs to the branch that is passed-in.
# Each new branch added halves the vertex count and edge length until the 
# count reaches one, and recursive iteration terminates.
def create_branches(bm, curr_branch, count, random_bend_range, branch_split_prob, vert_diff, tree):
    # If the vertex count is one, we've reached our terminal condition
    if count == 1:
        return
    
    # On creation of a new branch, cut both the vertext count and edge length in half
    new_branch_count = math.floor(count / 2)
    new_vert_diff = Vector((vert_diff.x/2, vert_diff.y/2, vert_diff.z/2))
    
    for vert in curr_branch:
        # Test if a new branch should be created/extruded from this vert
        if should_create_branch(branch_split_prob):
            # Create a new branch, extending from the current branch
            new_branch = create_branch(bm, new_branch_count, random_bend_range, vert, new_vert_diff)
            # tree & tree_node are for tracking the verticies for later iteration
            tree_node = MagicTreeNode(tree, indicies_from_branch(new_branch))
            tree.set_child_node(tree_node)
            
            # Recursivly create sub-branches on this new branch
            create_branches(bm, new_branch, new_branch_count, random_bend_range, branch_split_prob, new_vert_diff, tree_node)
            
    return

# Recursive function to resize the skin of each branch
# Reduces the resize factor by half for each recursive call
def resize_branch_skin(resize_factor, obj, tree):
    # Deselect any verticies that were previously selected
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Select only the verticies in this node's branch
    for i in tree.node_branch:
        obj.data.vertices[i].select = True
    
    # Every node iteration resizes the skin of it's branch by half.
    new_fac = resize_factor/2
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.skin_resize(value=(new_fac, new_fac, new_fac))
    
    for child_node in tree.child_nodes:
        resize_branch_skin(new_fac, obj, child_node)
    
###
# Pluggin class wrapper
###
class CreateMagicFractalTree(bpy.types.Operator):
    """Create a Magic Fractal Tree"""
    bl_idname = "mesh.add_magic_fractal_tree"
    bl_label = "Create Magic Fractal Tree"
    bl_options = {'REGISTER','UNDO'}
    
    count: bpy.props.IntProperty(name="Branch Count", default=20, min=5, max=50)
    random_bend_range: bpy.props.IntProperty(name="Bend Range", default=60, min=5, max=120,
                                     description="Expressed in degrees")
    branch_split_prob: bpy.props.FloatProperty(name="Branch Split Probability", default=0.5, min=0.0, max=1.0,
                        precision=1, description="Chance of sub-branch creation")
    initial_branch_radius: bpy.props.FloatProperty(name="Initial Branch Radius", default=0.15, min=0.01, max=1.0,
                        precision=2, description="Radius used for the skin modifier")             
    reduce_branch_radius: bpy.props.BoolProperty(name="Reduce Branch Radius", default=False,
        description="Recursivly redusing the branch radius is VERY time-comsuming. Ony enable this if count is < 20")
    
    def execute(self, context):
        bm = bmesh.new()
        starting_vert = bm.verts.new(noise.random_vector().normalized())

        # Create the 'root' branch
        root_branch = create_branch(bm, self.count, self.random_bend_range, starting_vert, starting_vert.co)
        tree = MagicTreeNode(None, indicies_from_branch(root_branch))
        tree.node_branch.insert(0, 0) # Starting vert is not included in the root branch so add it here

        # Create sub-branches extending from the root branch.
        create_branches(bm, root_branch, self.count, self.random_bend_range, self.branch_split_prob, starting_vert.co, tree)

        # Ensure indicies are accurate before converting to mesh data
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        mesh_data = bpy.data.meshes.new("MagicFractalTree")
        bm.to_mesh(mesh_data)
        bm.free()
        tree_obj = bpy.data.objects.new(mesh_data.name, mesh_data)
        context.collection.objects.link(tree_obj)

        # Make sure the object is selected and made active
        context.view_layer.objects.active = tree_obj
        tree_obj.select_set(True)

        # Apply skin modifier post-mesh creation
        skin_mod = tree_obj.modifiers.new(type='SKIN', name="Skin")
        skin_mod.use_smooth_shade = True
        skin_mod.branch_smoothing = 1.0

        # Apply subsurface modifier for smoothing
        subsurf_mod = tree_obj.modifiers.new(type='SUBSURF', name="Subsurface")
        subsurf_mod.levels = 3
        subsurf_mod.render_levels = 3

        if self.reduce_branch_radius:
            # Iterate through the tree to shrink the vertex radius of the skin modifier
            # (this must be done in edit mode using UI operations until a better solution is found)
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type="VERT")
    
            bpy.ops.object.mode_set(mode='OBJECT')
            resize_branch_skin(self.initial_branch_radius, tree_obj, tree)
    
            bpy.ops.object.mode_set(mode='OBJECT')

        else:
            # All branches will have an equal skin radius (this is a LOT faster)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.skin_resize(value=(self.initial_branch_radius, self.initial_branch_radius, self.initial_branch_radius))
            bpy.ops.object.mode_set(mode='OBJECT')
            
        return {'FINISHED'}


# Registration
def add_object_button(self, context):
    self.layout.operator(
        CreateMagicFractalTree.bl_idname,
        text="Add Magic Fractal Tree",
        icon='PLUGIN')

def register():
    bpy.utils.register_class(CreateMagicFractalTree)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)

def unregister():
    bpy.utils.unregister_class(CreateMagicFractalTree)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)

if __name__ == "__main__":
    register()