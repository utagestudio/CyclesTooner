import bpy

CYCLES_TOONER_OPACITY_PROP = "cyclestooner_opacity"
CYCLES_TOONER_OPACITY_NODE = "CyclesTooner_Opacity"
CYCLES_TOONER_ALPHA_MULTIPLY_NODE = "CyclesTooner_AlphaOpacity"
CYCLES_TOONER_TRANSPARENCY_NODE = "CyclesTooner_Transparency"
CYCLES_TOONER_MIX_NODE = "CyclesTooner_OpacityMix"
CYCLES_TOONER_TRANSPARENT_NODE = "CyclesTooner_Transparent"
OUTLINE_MATERIAL_NAME = "Toon_Outline"


def clamp_opacity(value):
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
            if mat and mat.name != OUTLINE_MATERIAL_NAME and mat.name not in seen:
                seen.add(mat.name)
                yield mat


def update_material_opacity_property(self, context):
    if self.name == OUTLINE_MATERIAL_NAME:
        return
    opacity = clamp_opacity(getattr(self, "cyclestooner_opacity", 1.0))
    set_material_opacity(self, opacity)


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


def sync_material_opacity_property(mat, opacity):
    if not hasattr(mat, "cyclestooner_opacity"):
        return

    mat["cyclestooner_skip_update"] = True
    try:
        mat.cyclestooner_opacity = clamp_opacity(opacity)
    finally:
        if "cyclestooner_skip_update" in mat:
            del mat["cyclestooner_skip_update"]


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
        opacity_node.location = (toon_node.location.x + 180, toon_node.location.y + 180)
    opacity_node.outputs['Value'].default_value = opacity

    transparent_node = nodes.get(CYCLES_TOONER_TRANSPARENT_NODE)
    if not transparent_node or transparent_node.type != 'BSDF_TRANSPARENT':
        transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
        transparent_node.name = CYCLES_TOONER_TRANSPARENT_NODE
        transparent_node.label = "CyclesTooner Transparent"
        transparent_node.location = (toon_node.location.x + 220, toon_node.location.y - 180)

    mix_node = nodes.get(CYCLES_TOONER_MIX_NODE)
    if not mix_node or mix_node.type != 'MIX_SHADER':
        mix_node = nodes.new(type='ShaderNodeMixShader')
        mix_node.name = CYCLES_TOONER_MIX_NODE
        mix_node.label = "CyclesTooner Opacity Mix"
        mix_node.location = (toon_node.location.x + 520, toon_node.location.y)

    effective_opacity_socket = opacity_node.outputs['Value']

    if alpha_source:
        alpha_multiply_node = nodes.get(CYCLES_TOONER_ALPHA_MULTIPLY_NODE)
        if not alpha_multiply_node or alpha_multiply_node.type != 'MATH':
            alpha_multiply_node = nodes.new(type='ShaderNodeMath')
            alpha_multiply_node.name = CYCLES_TOONER_ALPHA_MULTIPLY_NODE
            alpha_multiply_node.label = "CyclesTooner Alpha x Opacity"
            alpha_multiply_node.location = (toon_node.location.x + 300, toon_node.location.y + 120)
        alpha_multiply_node.operation = 'MULTIPLY'
        _replace_input_link(links, alpha_multiply_node.inputs[0], alpha_source)
        _replace_input_link(links, alpha_multiply_node.inputs[1], opacity_node.outputs['Value'])
        effective_opacity_socket = alpha_multiply_node.outputs['Value']

    transparency_node = nodes.get(CYCLES_TOONER_TRANSPARENCY_NODE)
    if not transparency_node or transparency_node.type != 'MATH':
        transparency_node = nodes.new(type='ShaderNodeMath')
        transparency_node.name = CYCLES_TOONER_TRANSPARENCY_NODE
        transparency_node.label = "CyclesTooner Transparency"
        transparency_node.location = (toon_node.location.x + 420, toon_node.location.y + 60)
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
            return False

        # 出力ノードの 'Surface' 入力を取得
        surface_input = output_node.inputs.get('Surface')
        if not surface_input or not surface_input.is_linked:
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

        if principled_node.type != 'BSDF_PRINCIPLED':
            return False
            
        # --- ここから変換処理 ---
        
        # 新しい Toon BSDF ノードを作成
        toon_node = nodes.new(type='ShaderNodeBsdfToon')
        toon_node.location = (principled_node.location.x, principled_node.location.y - 200)
        toon_node.inputs['Size'].default_value = 0.8
        
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
        if hasattr(mat, "blend_method"):
            mat.blend_method = 'OPAQUE'
        sync_material_opacity_property(mat, 1.0)
            
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
