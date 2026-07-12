import bpy

OUTLINE_SOURCE_SUFFIX = "_Outline_Source"
OUTLINE_CONTAINER_SUFFIX = "_Outline_Collection"
MODEL_COLLECTION_SUFFIX = "_Collection"
OUTLINE_ROOT_PROPERTY = "cyclestooner_outline_root_object"
OUTLINE_SOURCE_PROPERTY = "cyclestooner_outline_source_collection"
OUTLINE_OBJECT_PROPERTY = "cyclestooner_outline_object"
OUTLINE_MODIFIER_NAME = "ToonOutlineGN"
OUTLINE_MATERIAL_NAME = "Toon_Outline"
OUTLINE_MATERIAL_PROPERTY = "cyclestooner_outline_material"


def get_outline_base_name(target_collection):
    if target_collection.name.endswith(OUTLINE_SOURCE_SUFFIX):
        return target_collection.name.removesuffix(OUTLINE_SOURCE_SUFFIX)
    return target_collection.name


def get_outline_source_collection_name(target):
    name = target.name if hasattr(target, "name") else str(target)
    if name.endswith(OUTLINE_SOURCE_SUFFIX):
        return name
    return f"{name}{OUTLINE_SOURCE_SUFFIX}"


def get_outline_container_collection_name(target):
    name = target.name if hasattr(target, "name") else str(target)
    return f"{name}{OUTLINE_CONTAINER_SUFFIX}"


def get_model_collection_name(target):
    name = target.name if hasattr(target, "name") else str(target)
    return f"{name}{MODEL_COLLECTION_SUFFIX}"


def get_outline_target_name(outline_obj):
    if outline_obj and outline_obj.name.endswith("_Outline"):
        return outline_obj.name.removesuffix("_Outline")
    return None


def get_outline_object_name(target_collection):
    return f"{get_outline_base_name(target_collection)}_Outline"


def get_outline_mesh_name(target):
    name = target.name if hasattr(target, "name") else str(target)
    return f"{name}_Outline_Mesh"


def get_outline_node_group_name(target):
    name = target.name if hasattr(target, "name") else str(target)
    return f"GN_Outline_{name}"


def get_outline_material_name(target):
    name = target.name if hasattr(target, "name") else str(target)
    return f"{name}_Outline_Material"


def is_outline_material(mat):
    return bool(mat and (mat.get(OUTLINE_MATERIAL_PROPERTY) or mat.name == OUTLINE_MATERIAL_NAME))


def get_root_object(obj):
    root = obj
    while root and root.parent:
        root = root.parent
    return root


def collect_root_hierarchy_objects(root_obj):
    objects = []

    def visit(obj):
        objects.append(obj)
        for child in obj.children:
            visit(child)

    visit(root_obj)
    return objects


def find_object_parent_collection(obj, preferred_collection, scene_collection):
    if preferred_collection and obj.name in preferred_collection.objects:
        return preferred_collection
    if obj.users_collection:
        return obj.users_collection[0]
    return scene_collection


def find_parent_collection(target_collection, scene_collection):
    for col in bpy.data.collections:
        if target_collection.name in col.children:
            return col
    return scene_collection


def link_collection_once(parent_collection, child_collection):
    if parent_collection == child_collection:
        return
    if not any(collection == child_collection for collection in parent_collection.children):
        parent_collection.children.link(child_collection)


def unlink_collection_child(parent_collection, child_collection):
    if not parent_collection or parent_collection == child_collection:
        return
    if not any(collection == child_collection for collection in parent_collection.children):
        return
    parent_collection.children.unlink(child_collection)


def get_or_create_collection(name):
    collection = bpy.data.collections.get(name)
    if collection:
        return collection
    return bpy.data.collections.new(name)


def clear_collection_objects(collection):
    for obj in list(collection.objects):
        collection.objects.unlink(obj)


def ensure_root_model_collection(root_obj, parent_collection):
    model_name = get_model_collection_name(root_obj)
    model_collection = get_or_create_collection(model_name)
    link_collection_once(parent_collection, model_collection)

    for obj in collect_root_hierarchy_objects(root_obj):
        if obj.name not in model_collection.objects:
            model_collection.objects.link(obj)
        for collection in list(obj.users_collection):
            if collection == model_collection:
                continue
            collection.objects.unlink(obj)

    return model_collection


def find_outline_object(target_collection):
    outline_name = target_collection.get(OUTLINE_OBJECT_PROPERTY)
    if outline_name:
        outline_obj = bpy.data.objects.get(outline_name)
        if outline_obj:
            return outline_obj
    return bpy.data.objects.get(get_outline_object_name(target_collection))


def collection_contains_object(collection, obj):
    return any(candidate == obj for candidate in collection.all_objects)


def view_layer_contains_object(view_layer, obj):
    return any(candidate == obj for candidate in view_layer.objects)


def find_outline_collection_for_object(obj, preferred_collection=None):
    if not obj:
        return None
    root_obj = get_root_object(obj)
    for collection in bpy.data.collections:
        if not collection.get(OUTLINE_OBJECT_PROPERTY):
            continue
        if collection.get(OUTLINE_ROOT_PROPERTY) == root_obj.name:
            return collection
        if collection_contains_object(collection, obj):
            return collection

    if (
        preferred_collection
        and collection_contains_object(preferred_collection, obj)
        and find_outline_object(preferred_collection)
    ):
        return preferred_collection

    candidate_collections = []
    for collection in bpy.data.collections:
        if not collection_contains_object(collection, obj):
            continue
        if find_outline_object(collection):
            candidate_collections.append(collection)

    if not candidate_collections:
        return None
    return min(candidate_collections, key=lambda collection: len(collection.all_objects))


def find_outline_modifier(outline_obj):
    mod = outline_obj.modifiers.get(OUTLINE_MODIFIER_NAME)
    if mod and mod.type == 'NODES' and mod.node_group:
        return mod
    for candidate in outline_obj.modifiers:
        if candidate.type == 'NODES' and candidate.node_group:
            return candidate
    return None


def get_node_group_input_identifier(group, name):
    if hasattr(group, 'interface'):
        for item in group.interface.items_tree:
            if item.name == name:
                return item.identifier
    elif hasattr(group, 'inputs'):
        for item in group.inputs:
            if item.name == name:
                return item.identifier
    return None


def set_modifier_input(mod, name, value):
    if not mod or not mod.node_group:
        return False
    identifier = get_node_group_input_identifier(mod.node_group, name)
    if not identifier:
        return False
    mod[identifier] = value
    return True


def is_outline_excluded_object(obj, view_layer):
    if obj.type != 'MESH':
        return True
    if obj.name.endswith("_Outline"):
        return True
    try:
        if obj.hide_get(view_layer=view_layer):
            return True
    except TypeError:
        if obj.hide_get():
            return True
    if obj.hide_viewport:
        return True
    if hasattr(obj, "visible_get"):
        try:
            if not obj.visible_get(view_layer=view_layer):
                return True
        except TypeError:
            if not obj.visible_get():
                return True
    return False


def collect_visible_outline_objects(target_collection, view_layer):
    objects = []
    for obj in target_collection.all_objects:
        if is_outline_excluded_object(obj, view_layer):
            continue
        objects.append(obj)
    return objects


def collect_visible_root_outline_objects(root_obj, view_layer):
    objects = []

    def visit(obj):
        if not is_outline_excluded_object(obj, view_layer):
            objects.append(obj)
        for child in obj.children:
            visit(child)

    visit(root_obj)
    return objects


def link_outline_source_objects(source_collection, source_objects):
    linked_count = 0
    for obj in source_objects:
        if not source_collection.objects.get(obj.name):
            source_collection.objects.link(obj)
            linked_count += 1
    return linked_count


def create_filtered_outline_collection(target_collection, parent_collection, view_layer):
    source_objects = collect_visible_outline_objects(target_collection, view_layer)
    if not source_objects:
        return None, 0

    source_name = get_outline_source_collection_name(target_collection)
    source_collection = get_or_create_collection(source_name)
    clear_collection_objects(source_collection)
    link_collection_once(parent_collection, source_collection)

    linked_count = link_outline_source_objects(source_collection, source_objects)

    return source_collection, linked_count


def create_root_outline_collections(root_obj, parent_collection, view_layer):
    source_objects = collect_visible_root_outline_objects(root_obj, view_layer)
    if not source_objects:
        return None, 0

    model_collection = ensure_root_model_collection(root_obj, parent_collection)
    container_name = get_outline_container_collection_name(root_obj)
    container_collection = get_or_create_collection(container_name)
    link_collection_once(model_collection, container_collection)
    if parent_collection != model_collection:
        unlink_collection_child(parent_collection, container_collection)

    source_name = get_outline_source_collection_name(root_obj)
    source_collection = get_or_create_collection(source_name)
    clear_collection_objects(source_collection)
    source_collection[OUTLINE_ROOT_PROPERTY] = root_obj.name
    source_collection[OUTLINE_OBJECT_PROPERTY] = get_outline_object_name(source_collection)
    link_collection_once(container_collection, source_collection)

    linked_count = link_outline_source_objects(source_collection, source_objects)
    return source_collection, linked_count


def remove_outline_source_collection(collection_name):
    source_collection = bpy.data.collections.get(collection_name)
    if not source_collection:
        return False
    bpy.data.collections.remove(source_collection)
    return True


def remove_outline_container_if_empty(container_name):
    container_collection = bpy.data.collections.get(container_name)
    if not container_collection:
        return False
    if container_collection.objects or container_collection.children:
        return False
    bpy.data.collections.remove(container_collection)
    return True


def remove_unused_outline_data_blocks(root_name):
    mesh = bpy.data.meshes.get(get_outline_mesh_name(root_name))
    if mesh and mesh.users == 0:
        bpy.data.meshes.remove(mesh)

    node_group = bpy.data.node_groups.get(get_outline_node_group_name(root_name))
    if node_group and node_group.users == 0:
        bpy.data.node_groups.remove(node_group)


def resolve_outline_target_collection(context, selected_objects):
    if not selected_objects:
        return None

    active_obj = context.active_object
    if active_obj not in selected_objects:
        return None

    source_name = active_obj.get(OUTLINE_SOURCE_PROPERTY)
    if source_name:
        source_collection = bpy.data.collections.get(source_name)
        if source_collection:
            return source_collection

    target_name = get_outline_target_name(active_obj)
    if target_name:
        target_collection = bpy.data.collections.get(target_name)
        if not target_collection:
            target_collection = bpy.data.collections.get(get_outline_source_collection_name(target_name))
        if target_collection:
            return target_collection
        return None

    if active_obj:
        return find_outline_collection_for_object(active_obj, context.collection)

    return None


class OBJECT_OT_AddOutline(bpy.types.Operator):
    """
    選択したコレクションのアウトライン用メッシュを作成・設定するオペレーター
    Cycleレンダラー向けの背面法アウトラインを実現します。
    """
    bl_idname = "object.add_toon_outline"
    bl_label = "Add Outline"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objects = list(context.selected_objects)
        active_obj = context.active_object
        if not selected_objects or active_obj not in selected_objects:
            self.report({'WARNING'}, "アウトライン対象のオブジェクトを選択してください。")
            return {'CANCELLED'}

        root_obj = get_root_object(active_obj)
        parent_collection = find_object_parent_collection(root_obj, context.collection, context.scene.collection)
        outline_name = f"{root_obj.name}_Outline"
        if bpy.data.objects.get(outline_name):
            self.report({'WARNING'}, "このルートオブジェクトのアウトラインは既に存在します。Refresh Outlineを使用してください。")
            return {'CANCELLED'}
        remove_unused_outline_data_blocks(root_obj.name)

        source_collection, source_count = create_root_outline_collections(
            root_obj,
            parent_collection,
            context.view_layer,
        )

        if source_count == 0:
            self.report({'WARNING'}, "アウトライン対象の表示メッシュが見つかりませんでした。")
            return {'CANCELLED'}

        # 1. アウトライン用メッシュとオブジェクトの作成
        mesh_name = get_outline_mesh_name(root_obj)
        obj_name = outline_name
        
        # メッシュデータ作成（空）
        mesh = bpy.data.meshes.new(mesh_name)
        obj = bpy.data.objects.new(obj_name, mesh)
        
        # コレクションにリンク（ルート専用アウトライン管理コレクション内に配置）
        container_collection = bpy.data.collections.get(get_outline_container_collection_name(root_obj))
        if container_collection:
            container_collection.objects.link(obj)
        else:
            parent_collection.objects.link(obj)
        source_collection[OUTLINE_OBJECT_PROPERTY] = obj.name
        obj[OUTLINE_SOURCE_PROPERTY] = source_collection.name
        obj[OUTLINE_ROOT_PROPERTY] = root_obj.name
        
        # 2. マテリアルの作成・設定
        mat_name = get_outline_material_name(root_obj)
        mat = bpy.data.materials.new(name=mat_name)
        mat[OUTLINE_MATERIAL_PROPERTY] = True
        mat.use_nodes = True
        self._setup_outline_material(mat)
        
        # マテリアルをオブジェクトに追加
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
            
        # 3. オブジェクトプロパティ設定 (可視性)
        # Cycles設定: DiffuseとShadowのRay Visibilityをオフにする
        obj.visible_diffuse = False
        obj.visible_shadow = False
        # ビューポートでの選択を不可にする (Selectable)
        obj.hide_select = True
        
        # 4. ジオメトリノードの設定
        mod = obj.modifiers.new(name=OUTLINE_MODIFIER_NAME, type='NODES')
        node_group = self._create_geometry_node_group(get_outline_node_group_name(root_obj), mat)
        mod.node_group = node_group
        
        if not set_modifier_input(mod, 'Collection', source_collection):
            self.report({'WARNING'}, "アウトラインのCollection入力を設定できませんでした。")
            bpy.data.objects.remove(obj, do_unlink=True)
            if mat.users == 0 and is_outline_material(mat):
                bpy.data.materials.remove(mat)
            remove_outline_source_collection(source_collection.name)
            remove_outline_container_if_empty(get_outline_container_collection_name(root_obj))
            return {'CANCELLED'}
        set_modifier_input(mod, 'Value', 0.002)
        set_modifier_input(mod, 'Weight', 0.5)

        context.view_layer.update()

        # オブジェクトを選択状態にする
        bpy.ops.object.select_all(action='DESELECT')
        if view_layer_contains_object(context.view_layer, obj):
            obj.select_set(True)
            context.view_layer.objects.active = obj
        
        self.report({'INFO'}, f"ルートオブジェクト '{root_obj.name}' のアウトラインを作成しました。({source_count} meshes)")
        return {'FINISHED'}

    def _setup_outline_material(self, mat):
        """アウトライン用マテリアル（背面法用）のノード構築"""
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        nodes.clear()
        
        # Output
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (300, 0)
        
        # Mix Shader
        mix = nodes.new('ShaderNodeMixShader')
        mix.location = (0, 0)
        
        # Geometry Info (Backfacing)
        geo = nodes.new('ShaderNodeNewGeometry')
        geo.location = (-300, 200)
        
        # Transparent BSDF (表面は透明)
        trans = nodes.new('ShaderNodeBsdfTransparent')
        trans.location = (-300, 0)
        
        # Emission (裏面は発光＝アウトライン色)
        emis = nodes.new('ShaderNodeEmission')
        emis.location = (-300, -200)
        try:
            emis.inputs['Color'].default_value = (0.098, 0.035, 0.023, 1.0) # #190906
        except:
             # Fallback if indices are used
             pass
        emis.inputs['Strength'].default_value = 1.0
        
        # 接続
        links.new(geo.outputs['Backfacing'], mix.inputs['Fac'])
        links.new(trans.outputs['BSDF'], mix.inputs[1])
        links.new(emis.outputs['Emission'], mix.inputs[2])
        links.new(mix.outputs['Shader'], output.inputs['Surface'])

    def _create_geometry_node_group(self, name, mat):
        """ジオメトリノードグループを作成"""
        old_group = bpy.data.node_groups.get(name)
        if old_group and old_group.users == 0:
            bpy.data.node_groups.remove(old_group)
            
        group = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        
        # --- インターフェースの作成 (Blender 4.0+ API) ---
        # Collection Input
        group.interface.new_socket(name="Collection", in_out='INPUT', socket_type='NodeSocketCollection')
        
        # Weight Input
        socket_weight = group.interface.new_socket(name="Weight", in_out='INPUT', socket_type='NodeSocketFloat')
        socket_weight.default_value = 0.5
        
        # Value Input
        socket_value = group.interface.new_socket(name="Value", in_out='INPUT', socket_type='NodeSocketFloat')
        socket_value.default_value = 0.002
        
        # Geometry Output
        group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

        # --- ノードの作成 ---
        nodes = group.nodes
        links = group.links
        
        # Group Input / Output
        input_node = nodes.new('NodeGroupInput')
        input_node.location = (-600, 0)
        
        output_node = nodes.new('NodeGroupOutput')
        output_node.location = (600, 0)
        
        # Collection Info
        col_info = nodes.new('GeometryNodeCollectionInfo')
        col_info.location = (-400, 100)
        col_info.inputs['Separate Children'].default_value = False
        col_info.inputs['Reset Children'].default_value = False
        if hasattr(col_info, 'transform_space'):
            col_info.transform_space = 'RELATIVE'
            
        # Object Info
        obj_info = nodes.new('GeometryNodeObjectInfo')
        obj_info.location = (-400, -100)
        
        # Realize Instances
        realize = nodes.new('GeometryNodeRealizeInstances')
        realize.location = (-200, 100)
        
        # Set Position
        set_pos = nodes.new('GeometryNodeSetPosition')
        set_pos.location = (0, 100)
        
        # Set Material
        set_mat = nodes.new('GeometryNodeSetMaterial')
        set_mat.location = (200, 100)
        if mat:
            set_mat.inputs['Material'].default_value = mat
        
        # --- オフセット計算 ---
        # Normal
        normal = nodes.new('GeometryNodeInputNormal')
        normal.location = (-400, -300)
        
        # Multiply (Weight * Value)
        math_mul = nodes.new('ShaderNodeMath') 
        math_mul.operation = 'MULTIPLY'
        math_mul.location = (-400, -500)
        
        # Multiply (Normal * Scalar) -> Vector Math
        vec_mul = nodes.new('ShaderNodeVectorMath')
        vec_mul.operation = 'MULTIPLY'
        vec_mul.location = (-200, -300)
        
        # Add (Offset + 0.0001) -> Vector Math
        vec_add = nodes.new('ShaderNodeVectorMath')
        vec_add.operation = 'ADD'
        vec_add.location = (-100, -300)
        vec_add.inputs[1].default_value = (0.0001, 0.0001, 0.0001)
        
        # --- 接続 ---
        def get_socket(node, name, is_output=True):
            collection = node.outputs if is_output else node.inputs
            for s in collection:
                if s.name == name:
                    return s
            if len(collection) > 0:
                return collection[0]
            return None

        # Input Node Outputs
        socket_in_col = get_socket(input_node, 'Collection')
        socket_in_weight = get_socket(input_node, 'Weight')
        socket_in_value = get_socket(input_node, 'Value')
        
        # Connect Collection Info
        if socket_in_col:
            links.new(socket_in_col, col_info.inputs['Collection'])
        
        # Collection Info -> Realize Instances
        links.new(col_info.outputs['Instances'], realize.inputs['Geometry'])
        
        # Realize Instances -> Set Position
        links.new(realize.outputs['Geometry'], set_pos.inputs['Geometry'])
        
        # Offset Calculation
        if socket_in_weight and socket_in_value:
            links.new(socket_in_weight, math_mul.inputs[0])
            links.new(socket_in_value, math_mul.inputs[1])
        
        # Normal * (Weight * Value)
        links.new(normal.outputs['Normal'], vec_mul.inputs[0])
        links.new(math_mul.outputs['Value'], vec_mul.inputs[1])
        
        # Add small offset
        links.new(vec_mul.outputs['Vector'], vec_add.inputs[0])
        
        # Result -> Set Position Offset
        links.new(vec_add.outputs['Vector'], set_pos.inputs['Offset'])
        
        # Set Position -> Set Material
        links.new(set_pos.outputs['Geometry'], set_mat.inputs['Geometry'])
        
        # Set Material -> Group Output
        socket_out_geo = get_socket(output_node, 'Geometry', is_output=False)
        links.new(set_mat.outputs['Geometry'], socket_out_geo)
        
        return group


class OBJECT_OT_RefreshOutline(bpy.types.Operator):
    """
    既存アウトラインの参照元コレクションを現在の表示状態で再構築するオペレーター
    """
    bl_idname = "object.refresh_toon_outline"
    bl_label = "Refresh Outline"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.collection is not None or context.active_object is not None

    def execute(self, context):
        selected_objects = list(context.selected_objects)
        target_collection = resolve_outline_target_collection(context, selected_objects)
        if not target_collection:
            self.report({'WARNING'}, "更新対象のコレクションが見つかりませんでした。")
            return {'CANCELLED'}

        outline_obj = find_outline_object(target_collection)
        if not outline_obj:
            self.report({'WARNING'}, "更新対象のアウトラインが見つかりませんでした。先にAdd Outlineを実行してください。")
            return {'CANCELLED'}

        mod = find_outline_modifier(outline_obj)
        if not mod:
            self.report({'WARNING'}, "アウトラインのGeometry Nodesモディファイアが見つかりませんでした。")
            return {'CANCELLED'}
        if not get_node_group_input_identifier(mod.node_group, 'Collection'):
            self.report({'WARNING'}, "アウトラインのCollection入力が見つかりませんでした。")
            return {'CANCELLED'}

        root_name = target_collection.get(OUTLINE_ROOT_PROPERTY)
        root_obj = bpy.data.objects.get(root_name) if root_name else None
        source_objects = (
            collect_visible_root_outline_objects(root_obj, context.view_layer)
            if root_obj
            else collect_visible_outline_objects(target_collection, context.view_layer)
        )
        if not source_objects:
            self.report({'WARNING'}, "アウトライン対象の表示メッシュが見つかりませんでした。既存の対象は維持しました。")
            return {'CANCELLED'}

        if root_obj:
            parent_collection = find_object_parent_collection(root_obj, context.collection, context.scene.collection)
            source_collection, source_count = create_root_outline_collections(
                root_obj,
                parent_collection,
                context.view_layer,
            )
        else:
            parent_collection = find_parent_collection(target_collection, context.scene.collection)
            source_collection, source_count = create_filtered_outline_collection(
                target_collection,
                parent_collection,
                context.view_layer,
            )
        if not source_collection:
            self.report({'WARNING'}, "アウトライン対象の表示メッシュが見つかりませんでした。既存の対象は維持しました。")
            return {'CANCELLED'}
        if root_obj:
            source_collection[OUTLINE_OBJECT_PROPERTY] = outline_obj.name
            outline_obj[OUTLINE_SOURCE_PROPERTY] = source_collection.name
            outline_obj[OUTLINE_ROOT_PROPERTY] = root_obj.name

        if not set_modifier_input(mod, 'Collection', source_collection):
            self.report({'WARNING'}, "アウトラインのCollection入力を更新できませんでした。")
            return {'CANCELLED'}

        self.report({'INFO'}, f"コレクション '{target_collection.name}' のアウトライン対象を更新しました。({source_count} meshes)")
        return {'FINISHED'}


class OBJECT_OT_RemoveOutline(bpy.types.Operator):
    """
    アウトラインメッシュを削除し、不要になったリソースをクリーンアップするオペレーター
    """
    bl_idname = "object.remove_toon_outline"
    bl_label = "Remove Outline"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # 実行可能条件: オブジェクトが選択されている OR コレクションがアクティブ
        return bool(context.selected_objects) or bool(context.collection)

    def execute(self, context):
        objects_to_delete = []
        
        # 判定1: アクティブオブジェクトがアウトラインならそれを削除候補へ
        active_obj = context.active_object
        if active_obj and active_obj.name.endswith("_Outline"):
             objects_to_delete.append(active_obj)

        if not objects_to_delete and context.selected_objects:
            target_collection = resolve_outline_target_collection(context, list(context.selected_objects))
            if target_collection:
                target_obj = find_outline_object(target_collection)
                if target_obj:
                    objects_to_delete.append(target_obj)
        
        # 判定2: アウトラインの選択がなければ、選択コレクションから探す
        if not objects_to_delete and context.collection:
            coll_name = context.collection.name
            target_name = f"{coll_name}_Outline"
            target_obj = bpy.data.objects.get(target_name)
            if target_obj:
                objects_to_delete.append(target_obj)
        
        if not objects_to_delete:
            self.report({'WARNING'}, "削除対象のアウトラインが見つかりませんでした。")
            return {'CANCELLED'}

        # クリーンアップ対象のリソースを特定
        node_groups_to_check = set()
        meshes_to_check = set()
        materials_to_check = set()
        source_collections_to_remove = set()
        container_collections_to_remove = set()
        root_names_to_check = set()
        
        for obj in objects_to_delete:
            source_name = obj.get(OUTLINE_SOURCE_PROPERTY)
            if source_name:
                source_collections_to_remove.add(source_name)
            elif obj.name.endswith("_Outline"):
                source_collections_to_remove.add(f"{obj.name.removesuffix('_Outline')}{OUTLINE_SOURCE_SUFFIX}")

            root_name = obj.get(OUTLINE_ROOT_PROPERTY)
            if root_name:
                container_collections_to_remove.add(get_outline_container_collection_name(root_name))
                root_names_to_check.add(root_name)
            elif obj.name.endswith("_Outline"):
                root_names_to_check.add(obj.name.removesuffix("_Outline"))

            # Geometry Nodeの取得
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    node_groups_to_check.add(mod.node_group)

            if obj.data and obj.data.users <= 1:
                meshes_to_check.add(obj.data)
            
            # Materialの取得
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    materials_to_check.add(mat_slot.material)

        # オブジェクトの完全削除
        for obj in objects_to_delete:
            bpy.data.objects.remove(obj, do_unlink=True)

        remove_count_mesh = 0
        for mesh in meshes_to_check:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
                remove_count_mesh += 1

        remove_count_src = 0
        for collection_name in source_collections_to_remove:
            if remove_outline_source_collection(collection_name):
                remove_count_src += 1

        remove_count_container = 0
        for collection_name in container_collections_to_remove:
            if remove_outline_container_if_empty(collection_name):
                remove_count_container += 1
            
        # 削除後のクリーンアップ: ユーザー数が0になったリソースを削除
        remove_count_ng = 0
        for ng in node_groups_to_check:
            # 既に削除されている可能性や、usersカウントの更新を確認
            if ng.users == 0:
                bpy.data.node_groups.remove(ng)
                remove_count_ng += 1
                
        remove_count_mat = 0
        for mat in materials_to_check:
            if is_outline_material(mat) and mat.users == 0:
                bpy.data.materials.remove(mat)
                remove_count_mat += 1

        for root_name in root_names_to_check:
            remove_unused_outline_data_blocks(root_name)

        self.report({'INFO'}, f"アウトラインを削除しました。(Cleanup: Container={remove_count_container}, Src={remove_count_src}, Mesh={remove_count_mesh}, NG={remove_count_ng}, Mat={remove_count_mat})")
        return {'FINISHED'}
