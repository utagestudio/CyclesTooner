import bpy

OUTLINE_SOURCE_SUFFIX = "_Outline_Source"


def get_outline_source_collection_name(target_collection):
    return f"{target_collection.name}{OUTLINE_SOURCE_SUFFIX}"


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


def create_filtered_outline_collection(target_collection, parent_collection, view_layer):
    source_name = get_outline_source_collection_name(target_collection)
    old_collection = bpy.data.collections.get(source_name)
    if old_collection:
        bpy.data.collections.remove(old_collection)

    source_collection = bpy.data.collections.new(source_name)
    parent_collection.children.link(source_collection)

    linked_count = 0
    for obj in target_collection.all_objects:
        if is_outline_excluded_object(obj, view_layer):
            continue
        if not source_collection.objects.get(obj.name):
            source_collection.objects.link(obj)
            linked_count += 1

    return source_collection, linked_count


def remove_outline_source_collection(collection_name):
    source_collection = bpy.data.collections.get(collection_name)
    if not source_collection:
        return False
    bpy.data.collections.remove(source_collection)
    return True


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
        # アクティブなコレクションが存在するかチェック
        return context.collection is not None

    def execute(self, context):
        target_collection = context.collection
        
        # 親コレクションを探す（兄弟として配置するため）
        parent_collection = None
        for col in bpy.data.collections:
            if target_collection.name in col.children:
                parent_collection = col
                break
        
        # 親が見つからない場合（シーン直下の場合など）はシーンコレクションを使用
        if parent_collection is None:
            parent_collection = context.scene.collection

        source_collection, source_count = create_filtered_outline_collection(
            target_collection,
            parent_collection,
            context.view_layer,
        )

        if source_count == 0:
            remove_outline_source_collection(source_collection.name)
            self.report({'WARNING'}, "アウトライン対象の表示メッシュが見つかりませんでした。")
            return {'CANCELLED'}

        # 1. アウトライン用メッシュとオブジェクトの作成
        mesh_name = f"{target_collection.name}_Outline_Mesh"
        obj_name = f"{target_collection.name}_Outline"
        
        # メッシュデータ作成（空）
        mesh = bpy.data.meshes.new(mesh_name)
        obj = bpy.data.objects.new(obj_name, mesh)
        
        # コレクションにリンク（ターゲットコレクションの兄弟として）
        parent_collection.objects.link(obj)
        
        # 2. マテリアルの作成・設定
        mat_name = "Toon_Outline"
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
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
        mod = obj.modifiers.new(name="ToonOutlineGN", type='NODES')
        node_group = self._create_geometry_node_group(f"GN_Outline_{target_collection.name}")
        mod.node_group = node_group
        
        # モディファイアの入力値を設定
        # Blender 4.0以降 (含む 5.0) では socket.identifier を使用して確実にアクセスする
        
        # インターフェースから名前でidentifierを検索するヘルパー
        def get_identifier(group, name):
            # Blender 4.0+ API: interface.items_tree
            if hasattr(group, 'interface'):
                for item in group.interface.items_tree:
                    if item.name == name:
                        return item.identifier
            # Fallback for older API if needed (though user said 5.0)
            elif hasattr(group, 'inputs'):
                for item in group.inputs:
                    if item.name == name:
                        return item.identifier
            return None

        # Collection
        ident_col = get_identifier(node_group, 'Collection')
        if ident_col:
            mod[ident_col] = source_collection
            
        # Value
        ident_val = get_identifier(node_group, 'Value')
        if ident_val:
            mod[ident_val] = 0.002
            
        # Weight (Floatプロパティとして設定する場合はこちら)
        ident_weight = get_identifier(node_group, 'Weight')
        if ident_weight:
            mod[ident_weight] = 0.5

        # オブジェクトを選択状態にする
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        self.report({'INFO'}, f"コレクション '{target_collection.name}' のアウトラインを作成しました。({source_count} meshes)")
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

    def _create_geometry_node_group(self, name):
        """ジオメトリノードグループを作成"""
        # 既に存在する場合はリセットして再作成するか、既存を返す
        if name in bpy.data.node_groups:
            return bpy.data.node_groups[name]
            
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
        mat = bpy.data.materials.get("Toon_Outline")
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
        materials_to_check = set()
        source_collections_to_remove = set()
        
        for obj in objects_to_delete:
            if obj.name.endswith("_Outline"):
                source_collections_to_remove.add(f"{obj.name.removesuffix('_Outline')}{OUTLINE_SOURCE_SUFFIX}")

            # Geometry Nodeの取得
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    node_groups_to_check.add(mod.node_group)
            
            # Materialの取得
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    materials_to_check.add(mat_slot.material)

        # オブジェクトの完全削除
        for obj in objects_to_delete:
            bpy.data.objects.remove(obj, do_unlink=True)

        remove_count_src = 0
        for collection_name in source_collections_to_remove:
            if remove_outline_source_collection(collection_name):
                remove_count_src += 1
            
        # 削除後のクリーンアップ: ユーザー数が0になったリソースを削除
        remove_count_ng = 0
        for ng in node_groups_to_check:
            # 既に削除されている可能性や、usersカウントの更新を確認
            if ng.users == 0:
                bpy.data.node_groups.remove(ng)
                remove_count_ng += 1
                
        remove_count_mat = 0
        for mat in materials_to_check:
            # 安全のため、特定の名前のマテリアルのみをクリーンアップ
            if mat.name == "Toon_Outline" and mat.users == 0:
                bpy.data.materials.remove(mat)
                remove_count_mat += 1

        self.report({'INFO'}, f"アウトラインを削除しました。(Cleanup: Src={remove_count_src}, NG={remove_count_ng}, Mat={remove_count_mat})")
        return {'FINISHED'}
