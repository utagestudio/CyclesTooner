import bpy

CYCLES_TOONER_OPACITY_PROP = "cyclestooner_opacity"
CYCLES_TOONER_SMOOTH_PROP = "cyclestooner_smooth"
CYCLES_TOONER_OPACITY_NODE = "CyclesTooner_Opacity"
CYCLES_TOONER_ALPHA_MULTIPLY_NODE = "CyclesTooner_AlphaOpacity"
CYCLES_TOONER_TRANSPARENCY_NODE = "CyclesTooner_Transparency"
CYCLES_TOONER_MIX_NODE = "CyclesTooner_OpacityMix"
CYCLES_TOONER_TRANSPARENT_NODE = "CyclesTooner_Transparent"
CYCLES_TOONER_SOURCE_SHADER_PROP = "cyclestooner_source_shader"
CYCLES_TOONER_MMD_BASE_TEX = "CyclesTooner_MMDBaseTex"
CYCLES_TOONER_MMD_DIFFUSE_MULTIPLY = "CyclesTooner_MMDDiffuseMultiply"
CYCLES_TOONER_MTOON_BASE_TEX = "CyclesTooner_MToonBaseTex"
CYCLES_TOONER_MTOON_BASE_MULTIPLY = "CyclesTooner_MToonBaseMultiply"
OUTLINE_MATERIAL_NAME = "Toon_Outline"
OUTLINE_MATERIAL_PROPERTY = "cyclestooner_outline_material"
DEFAULT_TOON_SMOOTH = 0.2


def clamp_opacity(value):
    return max(0.0, min(1.0, float(value)))


def clamp_smooth(value):
    return max(0.0, min(1.0, float(value)))


def collect_selected_objects_recursive(selected_objects):
    objects_to_process = set()

    def collect_recursive(obj):
        objects_to_process.add(obj)
        for child in obj.children:
            collect_recursive(child)

    for obj in selected_objects:
        collect_recursive(obj)

    return objects_to_process


def iter_object_materials(objects):
    seen = set()
    for obj in objects:
        if not obj.data or not hasattr(obj.data, 'materials'):
            continue

        for slot in obj.material_slots:
            mat = slot.material
            if mat and not is_outline_material(mat) and mat.name not in seen:
                seen.add(mat.name)
                yield mat


def is_outline_material(mat):
    return bool(mat and (mat.get(OUTLINE_MATERIAL_PROPERTY) or mat.name == OUTLINE_MATERIAL_NAME))


def update_material_opacity_property(self, context):
    if is_outline_material(self):
        return
    opacity = clamp_opacity(getattr(self, "cyclestooner_opacity", 1.0))
    set_material_opacity(self, opacity)


def update_material_smooth_property(self, context):
    if is_outline_material(self):
        return
    smooth = clamp_smooth(getattr(self, "cyclestooner_smooth", DEFAULT_TOON_SMOOTH))
    set_material_smooth(self, smooth)


def set_material_opacity(mat, opacity):
    opacity = clamp_opacity(opacity)
    mat[CYCLES_TOONER_OPACITY_PROP] = opacity

    if hasattr(mat, "cyclestooner_opacity"):
        current = getattr(mat, "cyclestooner_opacity", None)
        if current is None or abs(current - opacity) > 0.0001:
            mat["cyclestooner_skip_update"] = True
            try:
                mat.cyclestooner_opacity = opacity
            finally:
                if "cyclestooner_skip_update" in mat:
                    del mat["cyclestooner_skip_update"]

    if mat.get("cyclestooner_skip_update"):
        return False

    if not mat.use_nodes or not mat.node_tree:
        return False

    opacity_node = mat.node_tree.nodes.get(CYCLES_TOONER_OPACITY_NODE)
    if opacity_node and opacity_node.type == 'VALUE':
        opacity_node.outputs['Value'].default_value = opacity
        _set_material_blend_settings(mat, opacity)
        return True

    return False


def set_material_smooth(mat, smooth):
    smooth = clamp_smooth(smooth)
    mat[CYCLES_TOONER_SMOOTH_PROP] = smooth

    if hasattr(mat, "cyclestooner_smooth"):
        current = getattr(mat, "cyclestooner_smooth", None)
        if current is None or abs(current - smooth) > 0.0001:
            mat["cyclestooner_skip_smooth_update"] = True
            try:
                mat.cyclestooner_smooth = smooth
            finally:
                if "cyclestooner_skip_smooth_update" in mat:
                    del mat["cyclestooner_skip_smooth_update"]

    if mat.get("cyclestooner_skip_smooth_update"):
        return False

    toon_node = find_cycles_toon_node(mat)
    if toon_node:
        apply_toon_smooth(mat, toon_node, smooth)
        return True

    return False


def sync_material_opacity_property(mat, opacity):
    if not hasattr(mat, "cyclestooner_opacity"):
        return

    mat["cyclestooner_skip_update"] = True
    try:
        mat.cyclestooner_opacity = clamp_opacity(opacity)
    finally:
        if "cyclestooner_skip_update" in mat:
            del mat["cyclestooner_skip_update"]


def sync_material_smooth_property(mat, smooth):
    if not hasattr(mat, "cyclestooner_smooth"):
        return

    mat["cyclestooner_skip_smooth_update"] = True
    try:
        mat.cyclestooner_smooth = clamp_smooth(smooth)
    finally:
        if "cyclestooner_skip_smooth_update" in mat:
            del mat["cyclestooner_skip_smooth_update"]


def _set_material_blend_settings(mat, opacity):
    if hasattr(mat, "blend_method"):
        mat.blend_method = 'BLEND' if opacity < 1.0 else 'OPAQUE'
    if hasattr(mat, "show_transparent_back"):
        mat.show_transparent_back = True


def find_output_node(nodes):
    """マテリアル出力ノードを探すヘルパーメソッド"""
    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
            output_node = node
            break
    if not output_node:
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                output_node = node
                break
    return output_node


def ensure_material_output_node(nodes, location=(400, 0)):
    output_node = find_output_node(nodes)
    if output_node:
        return output_node

    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = location
    return output_node


def find_cycles_tooner_mix_node(nodes):
    node = nodes.get(CYCLES_TOONER_MIX_NODE)
    if node and node.type == 'MIX_SHADER':
        return node

    for node in nodes:
        if node.type != 'MIX_SHADER':
            continue
        if node.name.startswith(CYCLES_TOONER_MIX_NODE):
            return node
        if node.label == "CyclesTooner Opacity Mix":
            return node

    return None


def repair_cycles_tooner_output(mat):
    if not mat.use_nodes or not mat.node_tree:
        return False

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mix_node = find_cycles_tooner_mix_node(nodes)
    if not mix_node:
        return False

    output_node = ensure_material_output_node(
        nodes,
        location=(mix_node.location.x + 330, mix_node.location.y + 20),
    )
    surface_input = output_node.inputs.get('Surface')
    shader_output = mix_node.outputs.get('Shader')
    if not surface_input or not shader_output:
        return False

    if surface_input.is_linked and surface_input.links[0].from_node == mix_node:
        return True

    _replace_input_link(links, surface_input, shader_output)
    output_node.location = (mix_node.location.x + 330, mix_node.location.y + 20)
    return True


def find_toon_node_from_root(root_node):
    if root_node.type == 'BSDF_TOON':
        return root_node

    if root_node.type != 'MIX_SHADER':
        return None

    for index in (1, 2):
        if len(root_node.inputs) > index and root_node.inputs[index].is_linked:
            node = root_node.inputs[index].links[0].from_node
            if node.type == 'BSDF_TOON':
                return node

    return None


def find_cycles_toon_node(mat):
    if not mat.use_nodes or not mat.node_tree:
        return None

    output_node = find_output_node(mat.node_tree.nodes)
    if not output_node:
        return None

    surface_input = output_node.inputs.get('Surface')
    if not surface_input or not surface_input.is_linked:
        return None

    return find_toon_node_from_root(surface_input.links[0].from_node)


def get_material_smooth(mat):
    return clamp_smooth(mat.get(CYCLES_TOONER_SMOOTH_PROP, getattr(mat, "cyclestooner_smooth", DEFAULT_TOON_SMOOTH)))


def apply_toon_smooth(mat, toon_node, smooth):
    smooth_input = toon_node.inputs.get('Smooth')
    if smooth_input:
        smooth_input.default_value = clamp_smooth(smooth)
        mat[CYCLES_TOONER_SMOOTH_PROP] = clamp_smooth(smooth)
        sync_material_smooth_property(mat, smooth)


def get_input_default(node, socket_name, fallback=None):
    if not node:
        return fallback
    socket = node.inputs.get(socket_name)
    if socket and hasattr(socket, "default_value"):
        return socket.default_value
    return fallback


def value_to_rgba(value, fallback=(1.0, 1.0, 1.0, 1.0)):
    try:
        values = tuple(value)
    except TypeError:
        return fallback

    if len(values) >= 4:
        return tuple(values[:4])
    if len(values) >= 3:
        return tuple(values[:3]) + (1.0,)
    return fallback


def get_nested_attr(obj, attr_path):
    current = obj
    for attr in attr_path.split("."):
        if current is None or not hasattr(current, attr):
            return None
        current = getattr(current, attr)
    return current


def find_image_texture_node_for_image(nodes, image):
    if image is None:
        return None
    for node in nodes:
        if node.type == 'TEX_IMAGE' and getattr(node, "image", None) == image:
            return node
    return None


def node_name_contains(node, patterns):
    node_tree_name = node.node_tree.name if node.type == 'GROUP' and node.node_tree else ""
    target = f"{node.name} {node.label} {node.bl_idname} {node_tree_name}".lower()
    return any(pattern in target for pattern in patterns)


def node_socket_names_contain(node, patterns):
    socket_names = " ".join([socket.name for socket in list(node.inputs) + list(node.outputs)]).lower()
    return any(pattern in socket_names for pattern in patterns)


def get_mmd_shader_node(nodes):
    node = nodes.get("mmd_shader")
    if node:
        return node

    for node in nodes:
        if node.name == "mmd_shader":
            return node
        if node.type == 'GROUP' and node.node_tree and node.node_tree.name.startswith("MMDShaderDev"):
            return node

    return None


def get_mtoon_extension(mat):
    extension = getattr(mat, "vrm_addon_extension", None)
    if not extension:
        return None

    for attr in ("mtoon1", "mtoon0", "mtoon"):
        mtoon = getattr(extension, attr, None)
        if mtoon:
            return mtoon

    return extension


def get_mtoon_shader_node(nodes):
    for node in nodes:
        if node.type == 'GROUP' and node_name_contains(node, ("mtoon",)):
            return node
        if node.type == 'GROUP' and node_socket_names_contain(node, ("lit color texture", "shade color texture", "shading shift texture")):
            return node
        if node_name_contains(node, ("mtoon",)):
            return node
    return None


def is_mtoon_shader_material(mat, root_node=None):
    if not mat.use_nodes or not mat.node_tree:
        return False

    if CYCLES_TOONER_OPACITY_NODE in mat.node_tree.nodes:
        return False

    mtoon_extension = get_mtoon_extension(mat)
    if mtoon_extension and (
        hasattr(mtoon_extension, "pbr_metallic_roughness")
        or hasattr(mtoon_extension, "base_color_factor")
        or hasattr(mtoon_extension, "shade_color_factor")
        or hasattr(mtoon_extension, "texture")
    ):
        return True

    if root_node and node_name_contains(root_node, ("mtoon",)):
        return True

    return get_mtoon_shader_node(mat.node_tree.nodes) is not None


def get_mtoon_base_color(mat, mtoon_extension, mtoon_node):
    attr_paths = (
        "pbr_metallic_roughness.base_color_factor",
        "base_color_factor",
        "lit_color_factor",
        "color",
    )
    for attr_path in attr_paths:
        value = get_nested_attr(mtoon_extension, attr_path)
        if value is not None:
            return value_to_rgba(value)

    for socket_name in ("Base Color", "Lit Color", "Color", "Diffuse Color"):
        value = get_input_default(mtoon_node, socket_name)
        if value is not None:
            return value_to_rgba(value)

    if len(mat.diffuse_color) >= 3:
        return value_to_rgba(mat.diffuse_color)

    return (1.0, 1.0, 1.0, 1.0)


def get_mtoon_alpha_value(mat, base_color):
    if len(base_color) > 3:
        return clamp_opacity(base_color[3])
    if len(mat.diffuse_color) > 3:
        return clamp_opacity(mat.diffuse_color[3])
    return 1.0


def get_mtoon_base_texture_node(mat, mtoon_extension):
    nodes = mat.node_tree.nodes

    image_attr_paths = (
        "pbr_metallic_roughness.base_color_texture.source",
        "pbr_metallic_roughness.base_color_texture.image",
        "base_color_texture.source",
        "base_color_texture.image",
        "main_texture.source",
        "main_texture.image",
        "texture.source",
        "texture.image",
    )
    for attr_path in image_attr_paths:
        image = get_nested_attr(mtoon_extension, attr_path)
        node = find_image_texture_node_for_image(nodes, image)
        if node:
            return node

    name_patterns = ("base", "main", "lit", "color", "texture")
    best_node = None
    for node in nodes:
        if node.type != 'TEX_IMAGE':
            continue
        name = f"{node.name} {node.label}".lower()
        if any(pattern in name for pattern in name_patterns):
            return node
        if not best_node:
            best_node = node

    return best_node


def build_mtoon_color_source(mat, toon_node, base_color, texture_node):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    if texture_node and texture_node.type == 'TEX_IMAGE':
        texture_node.name = CYCLES_TOONER_MTOON_BASE_TEX
        texture_node.label = "CyclesTooner MToon Base Texture"
        texture_node.location = (toon_node.location.x - 720, toon_node.location.y - 80)
        color_socket = texture_node.outputs.get("Color")
        if color_socket and not is_white_color(base_color):
            multiply_node = nodes.new(type='ShaderNodeMixRGB')
            multiply_node.name = CYCLES_TOONER_MTOON_BASE_MULTIPLY
            multiply_node.label = "CyclesTooner MToon Base"
            multiply_node.blend_type = 'MULTIPLY'
            multiply_node.inputs['Fac'].default_value = 1.0
            multiply_node.inputs['Color2'].default_value = base_color
            multiply_node.location = (toon_node.location.x - 360, toon_node.location.y)
            links.new(color_socket, multiply_node.inputs['Color1'])
            return multiply_node.outputs['Color']

        if color_socket:
            return color_socket

    toon_node.inputs['Color'].default_value = base_color
    return None


def collect_mtoon_shader_nodes_to_remove(nodes):
    nodes_to_remove = []
    keep_names = {CYCLES_TOONER_MTOON_BASE_TEX}

    for node in nodes:
        if node.name in keep_names:
            continue
        if node.type == 'GROUP' and node_name_contains(node, ("mtoon",)):
            nodes_to_remove.append(node)
        elif node.type == 'GROUP' and node_socket_names_contain(node, ("lit color texture", "shade color texture", "shading shift texture")):
            nodes_to_remove.append(node)
        elif node_name_contains(node, ("mtoon", "vrmtoon")):
            nodes_to_remove.append(node)

    return nodes_to_remove


def is_mmd_shader_material(mat, root_node=None):
    if not mat.use_nodes or not mat.node_tree:
        return False

    nodes = mat.node_tree.nodes
    mmd_shader_node = get_mmd_shader_node(nodes)
    if mmd_shader_node:
        return True

    if root_node and root_node.name == "mmd_shader":
        return True

    return bool(nodes.get("mmd_base_tex") and nodes.get("mmd_tex_uv"))


def get_mmd_diffuse_color(mat, mmd_shader_node):
    diffuse = get_input_default(mmd_shader_node, "Diffuse Color")
    if diffuse:
        return diffuse

    mmd_mat = getattr(mat, "mmd_material", None)
    if mmd_mat and hasattr(mmd_mat, "diffuse_color"):
        return tuple(mmd_mat.diffuse_color[:3]) + (1.0,)

    if len(mat.diffuse_color) >= 3:
        alpha = mat.diffuse_color[3] if len(mat.diffuse_color) > 3 else 1.0
        return tuple(mat.diffuse_color[:3]) + (alpha,)

    return (1.0, 1.0, 1.0, 1.0)


def get_mmd_alpha_value(mat, mmd_shader_node):
    alpha = get_input_default(mmd_shader_node, "Alpha")
    if alpha is not None:
        return clamp_opacity(alpha)

    mmd_mat = getattr(mat, "mmd_material", None)
    if mmd_mat and hasattr(mmd_mat, "alpha"):
        return clamp_opacity(mmd_mat.alpha)

    if len(mat.diffuse_color) > 3:
        return clamp_opacity(mat.diffuse_color[3])

    return 1.0


def get_texture_alpha_socket(texture_node):
    if not texture_node:
        return None

    alpha_socket = texture_node.outputs.get("Alpha")
    if alpha_socket:
        return alpha_socket

    return None


def is_white_color(color):
    return all(abs(float(channel) - 1.0) < 0.0001 for channel in color[:3])


def build_mmd_color_source(mat, toon_node, diffuse_color):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    texture_node = nodes.get("mmd_base_tex") or nodes.get(CYCLES_TOONER_MMD_BASE_TEX)

    if texture_node and texture_node.type == 'TEX_IMAGE':
        texture_node.name = CYCLES_TOONER_MMD_BASE_TEX
        texture_node.label = "CyclesTooner MMD Base Texture"
        texture_node.location = (toon_node.location.x - 720, toon_node.location.y - 80)
        color_socket = texture_node.outputs.get("Color")
        if color_socket and not is_white_color(diffuse_color):
            multiply_node = nodes.new(type='ShaderNodeMixRGB')
            multiply_node.name = CYCLES_TOONER_MMD_DIFFUSE_MULTIPLY
            multiply_node.label = "CyclesTooner MMD Diffuse"
            multiply_node.blend_type = 'MULTIPLY'
            multiply_node.inputs['Fac'].default_value = 1.0
            multiply_node.inputs['Color2'].default_value = diffuse_color
            multiply_node.location = (toon_node.location.x - 360, toon_node.location.y)
            links.new(color_socket, multiply_node.inputs['Color1'])
            return multiply_node.outputs['Color']

        if color_socket:
            return color_socket

    toon_node.inputs['Color'].default_value = diffuse_color
    return None


def get_source_opacity(mat, alpha_value):
    if CYCLES_TOONER_OPACITY_PROP in mat:
        return mat.get(CYCLES_TOONER_OPACITY_PROP, 1.0)
    if hasattr(mat, "cyclestooner_opacity"):
        opacity = getattr(mat, "cyclestooner_opacity", 1.0)
        if abs(opacity - 1.0) > 0.0001:
            return opacity
    return alpha_value


def collect_mmd_shader_nodes_to_remove(nodes):
    nodes_to_remove = []
    keep_names = {CYCLES_TOONER_MMD_BASE_TEX, "mmd_base_tex"}

    for node in nodes:
        if node.name in keep_names:
            continue
        if node.name.startswith("mmd_"):
            nodes_to_remove.append(node)
        elif node.type == 'GROUP' and node.node_tree and node.node_tree.name.startswith("MMDShaderDev"):
            nodes_to_remove.append(node)

    return nodes_to_remove


def get_alpha_source_from_principled(principled_node):
    alpha_input = principled_node.inputs.get('Alpha')
    if alpha_input and alpha_input.is_linked:
        return alpha_input.links[0].from_socket
    return None


def extract_alpha_source_from_mix_fac(fac_node, nodes_to_remove=None):
    if nodes_to_remove is None:
        nodes_to_remove = []

    if fac_node.type == 'INVERT':
        nodes_to_remove.append(fac_node)
        if fac_node.inputs['Color'].is_linked:
            return fac_node.inputs['Color'].links[0].from_socket
        return None

    if fac_node.name == CYCLES_TOONER_TRANSPARENCY_NODE and fac_node.type == 'MATH':
        nodes_to_remove.append(fac_node)
        if not fac_node.inputs[1].is_linked:
            return None

        effective_node = fac_node.inputs[1].links[0].from_node
        if effective_node.name == CYCLES_TOONER_ALPHA_MULTIPLY_NODE:
            nodes_to_remove.append(effective_node)
            opacity_node = effective_node.inputs[1].links[0].from_node if effective_node.inputs[1].is_linked else None
            if opacity_node and opacity_node.name == CYCLES_TOONER_OPACITY_NODE:
                nodes_to_remove.append(opacity_node)
            if effective_node.inputs[0].is_linked:
                return effective_node.inputs[0].links[0].from_socket
        elif effective_node.name == CYCLES_TOONER_OPACITY_NODE:
            nodes_to_remove.append(effective_node)

    return None


def get_alpha_source_from_root_mix(root_node):
    if root_node.type != 'MIX_SHADER':
        return None
    if not root_node.inputs[0].is_linked:
        return None
    return extract_alpha_source_from_mix_fac(root_node.inputs[0].links[0].from_node)


def collect_obsolete_mix_nodes(root_node):
    if root_node.type != 'MIX_SHADER' or root_node.name == CYCLES_TOONER_MIX_NODE:
        return []

    nodes_to_remove = [root_node]
    if root_node.inputs[0].is_linked:
        fac_node = root_node.inputs[0].links[0].from_node
        if fac_node.type == 'INVERT':
            nodes_to_remove.append(fac_node)

    if len(root_node.inputs) > 2 and root_node.inputs[2].is_linked:
        transparent_node = root_node.inputs[2].links[0].from_node
        if transparent_node.type == 'BSDF_TRANSPARENT':
            nodes_to_remove.append(transparent_node)

    return nodes_to_remove


def remove_nodes_if_present(nodes, nodes_to_remove):
    for node in nodes_to_remove:
        if nodes.get(node.name) == node:
            nodes.remove(node)


def collect_reachable_nodes_from_output(output_node):
    reachable = set()

    def visit_socket_input(input_socket):
        for link in input_socket.links:
            visit_node(link.from_node)

    def visit_node(node):
        if node.name in reachable:
            return
        reachable.add(node.name)
        for input_socket in node.inputs:
            visit_socket_input(input_socket)

    reachable.add(output_node.name)
    surface_input = output_node.inputs.get('Surface')
    if surface_input:
        visit_socket_input(surface_input)

    return reachable


def remove_unreachable_nodes_from_output(mat):
    if not mat.use_nodes or not mat.node_tree:
        return 0

    nodes = mat.node_tree.nodes
    output_node = find_output_node(nodes)
    if not output_node:
        return 0

    reachable = collect_reachable_nodes_from_output(output_node)
    nodes_to_remove = [node for node in nodes if node.name not in reachable]
    remove_count = 0

    for node in nodes_to_remove:
        if nodes.get(node.name) == node:
            nodes.remove(node)
            remove_count += 1

    return remove_count


def setup_toon_opacity_nodes(mat, toon_node, output_node, alpha_source=None, opacity=1.0):
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    opacity = clamp_opacity(opacity)

    opacity_node = nodes.get(CYCLES_TOONER_OPACITY_NODE)
    if not opacity_node or opacity_node.type != 'VALUE':
        opacity_node = nodes.new(type='ShaderNodeValue')
        opacity_node.name = CYCLES_TOONER_OPACITY_NODE
        opacity_node.label = "CyclesTooner Opacity"
    opacity_node.location = (toon_node.location.x - 420, toon_node.location.y + 170)
    opacity_node.outputs['Value'].default_value = opacity

    transparent_node = nodes.get(CYCLES_TOONER_TRANSPARENT_NODE)
    if not transparent_node or transparent_node.type != 'BSDF_TRANSPARENT':
        transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
        transparent_node.name = CYCLES_TOONER_TRANSPARENT_NODE
        transparent_node.label = "CyclesTooner Transparent"
    transparent_node.location = (toon_node.location.x, toon_node.location.y - 240)

    mix_node = find_cycles_tooner_mix_node(nodes)
    if not mix_node or mix_node.type != 'MIX_SHADER':
        mix_node = nodes.new(type='ShaderNodeMixShader')
        mix_node.name = CYCLES_TOONER_MIX_NODE
        mix_node.label = "CyclesTooner Opacity Mix"
    mix_node.location = (toon_node.location.x + 430, toon_node.location.y)

    effective_opacity_socket = opacity_node.outputs['Value']

    if alpha_source:
        alpha_multiply_node = nodes.get(CYCLES_TOONER_ALPHA_MULTIPLY_NODE)
        if not alpha_multiply_node or alpha_multiply_node.type != 'MATH':
            alpha_multiply_node = nodes.new(type='ShaderNodeMath')
            alpha_multiply_node.name = CYCLES_TOONER_ALPHA_MULTIPLY_NODE
            alpha_multiply_node.label = "CyclesTooner Alpha x Opacity"
        alpha_multiply_node.location = (toon_node.location.x - 200, toon_node.location.y + 170)
        alpha_multiply_node.operation = 'MULTIPLY'
        _replace_input_link(links, alpha_multiply_node.inputs[0], alpha_source)
        _replace_input_link(links, alpha_multiply_node.inputs[1], opacity_node.outputs['Value'])
        effective_opacity_socket = alpha_multiply_node.outputs['Value']

    transparency_node = nodes.get(CYCLES_TOONER_TRANSPARENCY_NODE)
    if not transparency_node or transparency_node.type != 'MATH':
        transparency_node = nodes.new(type='ShaderNodeMath')
        transparency_node.name = CYCLES_TOONER_TRANSPARENCY_NODE
        transparency_node.label = "CyclesTooner Transparency"
    transparency_node.location = (toon_node.location.x + 40, toon_node.location.y + 230)
    transparency_node.operation = 'SUBTRACT'
    transparency_node.use_clamp = True
    transparency_node.inputs[0].default_value = 1.0
    _replace_input_link(links, transparency_node.inputs[1], effective_opacity_socket)

    _replace_input_link(links, mix_node.inputs['Fac'], transparency_node.outputs['Value'])
    _replace_input_link(links, mix_node.inputs[1], toon_node.outputs['BSDF'])
    _replace_input_link(links, mix_node.inputs[2], transparent_node.outputs['BSDF'])
    _replace_input_link(links, output_node.inputs['Surface'], mix_node.outputs['Shader'])

    mat[CYCLES_TOONER_OPACITY_PROP] = opacity
    sync_material_opacity_property(mat, opacity)
    _set_material_blend_settings(mat, opacity)


def _replace_input_link(links, input_socket, output_socket):
    for link in list(input_socket.links):
        links.remove(link)
    links.new(output_socket, input_socket)


class OBJECT_OT_ToonConverter(bpy.types.Operator):
    """
    Principled BSDF を Toon BSDF に再帰的に変換するオペレーター
    選択されたオブジェクトと、そのすべての子オブジェクトに対して処理を行います。
    """
    bl_idname = "object.to_toon_converter"
    bl_label = "Convert"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """
        このオペレーターが実行可能かどうかを判定します。
        オブジェクトが少なくとも1つ選択されている場合のみTrueを返します。
        """
        return bool(context.selected_objects)

    def execute(self, context):
        """
        オペレーター実行時のメイン処理です。
        """
        # レンダーエンジンがEEVEE系ならCyclesに変更
        if context.scene.render.engine in ['BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT']:
            context.scene.render.engine = 'CYCLES'
            self.report({'INFO'}, "Render Engine switched to Cycles")

        # 処理対象のオブジェクトを収集（選択オブジェクト + その子孫すべて）
        objects_to_process = collect_selected_objects_recursive(context.selected_objects)
            
        # 収集したオブジェクトごとにマテリアル変換処理を実行
        processed_count = 0
        for mat in iter_object_materials(objects_to_process):
            if self.process_material(mat):
                processed_count += 1
        
        # 処理結果を情報エリアに報告
        self.report({'INFO'}, f"{len(objects_to_process)} 個のオブジェクトのマテリアルを Toon 化しました。")
        return {'FINISHED'}

    def process_material(self, mat):
        """
        1つのマテリアル内のノードを操作し、Principled BSDF を Toon BSDF に置換します。
        """
        # ノードを使用していないマテリアルは対象外
        if not mat.use_nodes or not mat.node_tree:
            return False
            
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        
        # マテリアル出力ノードを探す
        output_node = find_output_node(nodes)
        if not output_node:
            if repair_cycles_tooner_output(mat):
                return True
            if is_mtoon_shader_material(mat):
                return self.process_mtoon_material(mat, ensure_material_output_node(nodes))
            return False

        # 出力ノードの 'Surface' 入力を取得
        surface_input = output_node.inputs.get('Surface')
        if not surface_input or not surface_input.is_linked:
            if repair_cycles_tooner_output(mat):
                return True
            if is_mtoon_shader_material(mat):
                return self.process_mtoon_material(mat, output_node)
            return False
            
        # 接続されているリンクから元のノード（Principled BSDFであることを期待）を取得
        link = surface_input.links[0]
        principled_node = link.from_node

        # 接続先が Principled BSDF でない場合は何もしない
        if principled_node.type == 'MIX_SHADER':
            toon_node = find_toon_node_from_root(principled_node)
            if toon_node:
                alpha_source = get_alpha_source_from_root_mix(principled_node)
                obsolete_nodes = collect_obsolete_mix_nodes(principled_node)
                setup_toon_opacity_nodes(
                    mat,
                    toon_node,
                    output_node,
                    alpha_source=alpha_source,
                    opacity=mat.get(CYCLES_TOONER_OPACITY_PROP, getattr(mat, "cyclestooner_opacity", 1.0)),
                )
                remove_nodes_if_present(nodes, obsolete_nodes)
                return True

        if is_mmd_shader_material(mat, principled_node):
            return self.process_mmd_material(mat, output_node)

        if is_mtoon_shader_material(mat, principled_node):
            return self.process_mtoon_material(mat, output_node)

        if principled_node.type != 'BSDF_PRINCIPLED':
            return False
            
        # --- ここから変換処理 ---
        
        # 新しい Toon BSDF ノードを作成
        toon_node = nodes.new(type='ShaderNodeBsdfToon')
        toon_node.location = (principled_node.location.x, principled_node.location.y - 200)
        toon_node.inputs['Size'].default_value = 0.8
        apply_toon_smooth(mat, toon_node, get_material_smooth(mat))
        
        # --- Base Color (Color) の移行 ---
        base_color_input = principled_node.inputs.get('Base Color')
        if base_color_input:
            if base_color_input.is_linked:
                source = base_color_input.links[0].from_socket
                links.new(source, toon_node.inputs['Color'])
            else:
                toon_node.inputs['Color'].default_value = base_color_input.default_value
        
        # --- Normal の移行 ---
        normal_input = principled_node.inputs.get('Normal')
        if normal_input and normal_input.is_linked:
            source = normal_input.links[0].from_socket
            links.new(source, toon_node.inputs['Normal'])
            
        alpha_source = get_alpha_source_from_principled(principled_node)
        opacity = mat.get(CYCLES_TOONER_OPACITY_PROP, getattr(mat, "cyclestooner_opacity", 1.0))
        setup_toon_opacity_nodes(mat, toon_node, output_node, alpha_source=alpha_source, opacity=opacity)
        
        # 古いノードを削除
        nodes.remove(principled_node)
        
        return True

    def process_mmd_material(self, mat, output_node):
        tree = mat.node_tree
        nodes = tree.nodes

        mmd_shader_node = get_mmd_shader_node(nodes)
        diffuse_color = get_mmd_diffuse_color(mat, mmd_shader_node)
        alpha_value = get_mmd_alpha_value(mat, mmd_shader_node)
        base_texture_node = nodes.get("mmd_base_tex") or nodes.get(CYCLES_TOONER_MMD_BASE_TEX)

        toon_node = nodes.new(type='ShaderNodeBsdfToon')
        toon_node.location = (
            mmd_shader_node.location.x if mmd_shader_node else output_node.location.x - 400,
            (mmd_shader_node.location.y - 200) if mmd_shader_node else output_node.location.y - 200,
        )
        output_node.location = (toon_node.location.x + 760, toon_node.location.y + 20)
        toon_node.inputs['Size'].default_value = 0.8
        apply_toon_smooth(mat, toon_node, get_material_smooth(mat))

        color_source = build_mmd_color_source(mat, toon_node, diffuse_color)
        if color_source:
            tree.links.new(color_source, toon_node.inputs['Color'])

        texture_alpha_socket = get_texture_alpha_socket(base_texture_node)
        opacity = get_source_opacity(mat, alpha_value)
        setup_toon_opacity_nodes(mat, toon_node, output_node, alpha_source=texture_alpha_socket, opacity=opacity)

        mat[CYCLES_TOONER_SOURCE_SHADER_PROP] = "MMDShaderDev"
        remove_nodes_if_present(nodes, collect_mmd_shader_nodes_to_remove(nodes))
        repair_cycles_tooner_output(mat)

        return True

    def process_mtoon_material(self, mat, output_node):
        tree = mat.node_tree
        nodes = tree.nodes
        output_node = output_node or ensure_material_output_node(nodes)

        mtoon_extension = get_mtoon_extension(mat)
        mtoon_node = get_mtoon_shader_node(nodes)
        base_color = get_mtoon_base_color(mat, mtoon_extension, mtoon_node)
        alpha_value = get_mtoon_alpha_value(mat, base_color)
        base_texture_node = get_mtoon_base_texture_node(mat, mtoon_extension)

        toon_node = nodes.new(type='ShaderNodeBsdfToon')
        toon_node.location = (
            mtoon_node.location.x if mtoon_node else output_node.location.x - 400,
            (mtoon_node.location.y - 200) if mtoon_node else output_node.location.y - 200,
        )
        output_node.location = (toon_node.location.x + 760, toon_node.location.y + 20)
        toon_node.inputs['Size'].default_value = 0.8
        apply_toon_smooth(mat, toon_node, get_material_smooth(mat))

        color_source = build_mtoon_color_source(mat, toon_node, base_color, base_texture_node)
        if color_source:
            tree.links.new(color_source, toon_node.inputs['Color'])

        texture_alpha_socket = get_texture_alpha_socket(base_texture_node)
        opacity = get_source_opacity(mat, alpha_value)
        setup_toon_opacity_nodes(mat, toon_node, output_node, alpha_source=texture_alpha_socket, opacity=opacity)

        mat[CYCLES_TOONER_SOURCE_SHADER_PROP] = "MToon"
        remove_nodes_if_present(nodes, collect_mtoon_shader_nodes_to_remove(nodes))
        repair_cycles_tooner_output(mat)
        remove_unreachable_nodes_from_output(mat)

        return True


class OBJECT_OT_ToonReverter(bpy.types.Operator):
    """
    Toon BSDF (および関連する透明化セットアップ) を Principled BSDF に戻すオペレーター
    選択されたオブジェクトと、そのすべての子オブジェクトに対して処理を行います。
    """
    bl_idname = "object.to_toon_reverter"
    bl_label = "Revert"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        # 処理対象のオブジェクトを収集
        objects_to_process = collect_selected_objects_recursive(context.selected_objects)
            
        # 収集したオブジェクトごとにリバート処理を実行
        processed_count = 0
        for mat in iter_object_materials(objects_to_process):
            if self.revert_material(mat):
                processed_count += 1
        
        self.report({'INFO'}, f"{len(objects_to_process)} 個のオブジェクトのマテリアルを元に戻しました。")
        return {'FINISHED'}

    def revert_material(self, mat):
        """
        Toon化されたマテリアルを Principled BSDF に戻します。
        """
        if not mat.use_nodes or not mat.node_tree:
            return False
            
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        
        # 出力ノードを探す
        output_node = find_output_node(nodes)
        if not output_node:
            return False

        surface_input = output_node.inputs.get('Surface')
        if not surface_input or not surface_input.is_linked:
            return False
            
        # Outputに繋がっているノードを取得
        root_node = surface_input.links[0].from_node
        
        toon_node = None
        alpha_source = None
        nodes_to_remove = []
        
        # --- パターン判定 ---
        if root_node.type == 'MIX_SHADER':
            # Alpha対応の構成と推測される
            mix_node = root_node
            nodes_to_remove.append(mix_node)
            
            # Toonノードを探す
            if len(mix_node.inputs) > 1 and mix_node.inputs[1].is_linked:
                possible_toon = mix_node.inputs[1].links[0].from_node
                if possible_toon.type == 'BSDF_TOON':
                    toon_node = possible_toon
                    nodes_to_remove.append(toon_node)
            
            # Transparentノードを探す (削除用)
            if len(mix_node.inputs) > 2 and mix_node.inputs[2].is_linked:
                possible_trans = mix_node.inputs[2].links[0].from_node
                if possible_trans.type == 'BSDF_TRANSPARENT':
                    nodes_to_remove.append(possible_trans)
            
            # 新しい透明度ノード構成、または旧Invert構成からAlphaソースを探す
            if mix_node.inputs[0].is_linked:
                fac_node = mix_node.inputs[0].links[0].from_node
                alpha_source = extract_alpha_source_from_mix_fac(fac_node, nodes_to_remove)

        elif root_node.type == 'BSDF_TOON':
            # Alphaなしの単純Toon構成
            toon_node = root_node
            nodes_to_remove.append(toon_node)
            
        # Toonノードが見つからなければ、Toonerで変換されたものではないと判断
        if not toon_node:
            return False
            
        # --- 復元処理 ---
        
        # Principled BSDF を作成
        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.location = toon_node.location
        
        # Color -> Base Color
        toon_color_input = toon_node.inputs.get('Color')
        if toon_color_input:
            if toon_color_input.is_linked:
                source = toon_color_input.links[0].from_socket
                links.new(source, principled_node.inputs['Base Color'])
            else:
                principled_node.inputs['Base Color'].default_value = toon_color_input.default_value
        
        # Normal -> Normal
        toon_normal_input = toon_node.inputs.get('Normal')
        if toon_normal_input and toon_normal_input.is_linked:
            source = toon_normal_input.links[0].from_socket
            links.new(source, principled_node.inputs['Normal'])
            
        # Alpha
        if alpha_source:
            links.new(alpha_source, principled_node.inputs['Alpha'])
            
        # Output へ接続
        links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
        
        # 古いノード群を削除
        remove_nodes_if_present(nodes, nodes_to_remove)

        if CYCLES_TOONER_OPACITY_PROP in mat:
            del mat[CYCLES_TOONER_OPACITY_PROP]
        if CYCLES_TOONER_SMOOTH_PROP in mat:
            del mat[CYCLES_TOONER_SMOOTH_PROP]
        if CYCLES_TOONER_SOURCE_SHADER_PROP in mat:
            del mat[CYCLES_TOONER_SOURCE_SHADER_PROP]
        if hasattr(mat, "blend_method"):
            mat.blend_method = 'OPAQUE'
        sync_material_opacity_property(mat, 1.0)
        sync_material_smooth_property(mat, DEFAULT_TOON_SMOOTH)
            
        return True

class OBJECT_OT_SetToonOpacity(bpy.types.Operator):
    """
    選択されたオブジェクトと子孫のToon化済みマテリアルへ透明度を一括適用します。
    """
    bl_idname = "object.set_toon_opacity"
    bl_label = "Apply Opacity"
    bl_options = {'REGISTER', 'UNDO'}

    opacity: bpy.props.FloatProperty(
        name="Opacity",
        min=0.0,
        max=1.0,
        default=1.0,
        subtype='FACTOR',
    )

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        objects_to_process = collect_selected_objects_recursive(context.selected_objects)
        processed_count = 0

        for mat in iter_object_materials(objects_to_process):
            if self.apply_opacity_to_material(mat, self.opacity):
                processed_count += 1

        self.report({'INFO'}, f"{processed_count} 個のマテリアルに透明度を適用しました。")
        return {'FINISHED'}

    def apply_opacity_to_material(self, mat, opacity):
        if not mat.use_nodes or not mat.node_tree:
            return False

        nodes = mat.node_tree.nodes
        output_node = find_output_node(nodes)
        if not output_node:
            return False

        surface_input = output_node.inputs.get('Surface')
        if not surface_input or not surface_input.is_linked:
            return False

        root_node = surface_input.links[0].from_node
        toon_node = find_toon_node_from_root(root_node)
        if not toon_node:
            return False

        obsolete_nodes = collect_obsolete_mix_nodes(root_node)
        setup_toon_opacity_nodes(
            mat,
            toon_node,
            output_node,
            alpha_source=get_alpha_source_from_root_mix(root_node),
            opacity=opacity,
        )
        remove_nodes_if_present(nodes, obsolete_nodes)
        return True


class OBJECT_OT_SetToonSmooth(bpy.types.Operator):
    """
    選択されたオブジェクトと子孫のToon化済みマテリアルへSmoothを一括適用します。
    """
    bl_idname = "object.set_toon_smooth"
    bl_label = "Apply Smooth"
    bl_options = {'REGISTER', 'UNDO'}

    smooth: bpy.props.FloatProperty(
        name="Smooth",
        min=0.0,
        max=1.0,
        default=DEFAULT_TOON_SMOOTH,
        subtype='FACTOR',
    )

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        objects_to_process = collect_selected_objects_recursive(context.selected_objects)
        processed_count = 0

        for mat in iter_object_materials(objects_to_process):
            if set_material_smooth(mat, self.smooth):
                processed_count += 1

        self.report({'INFO'}, f"{processed_count} 個のマテリアルにSmoothを適用しました。")
        return {'FINISHED'}
