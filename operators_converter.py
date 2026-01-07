import bpy

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
        objects_to_process = set()
        
        def collect_recursive(obj):
            """
            再帰的に子オブジェクトを収集する内部関数
            """
            objects_to_process.add(obj)
            for child in obj.children:
                collect_recursive(child)
        
        # 選択された各オブジェクトに対して再帰収集を実行
        for obj in context.selected_objects:
            collect_recursive(obj)
            
        # 収集したオブジェクトごとにマテリアル変換処理を実行
        processed_count = 0
        for obj in objects_to_process:
            # マテリアルスロットを持たないオブジェクトはスキップ
            if not obj.data or not hasattr(obj.data, 'materials'):
                continue
                
            # 各マテリアルスロットを確認
            for slot in obj.material_slots:
                if slot.material:
                    # マテリアル変換処理を実行（成功したらカウントアップ）
                    if self.process_material(slot.material):
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
        output_node = self._find_output_node(nodes)
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
            
        # --- Alpha の処理 ---
        final_shader = toon_node.outputs['BSDF']
        
        alpha_input = principled_node.inputs.get('Alpha')
        if alpha_input and alpha_input.is_linked:
            alpha_source = alpha_input.links[0].from_socket
            
            # Alpha用ノード群の作成
            invert_node = nodes.new(type='ShaderNodeInvert')
            invert_node.location = (toon_node.location.x + 200, toon_node.location.y)
            links.new(alpha_source, invert_node.inputs['Color'])
            
            transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
            transparent_node.location = (toon_node.location.x + 200, toon_node.location.y - 150)
            
            mix_node = nodes.new(type='ShaderNodeMixShader')
            mix_node.location = (toon_node.location.x + 400, toon_node.location.y)
            
            # 接え
            links.new(invert_node.outputs['Color'], mix_node.inputs['Fac'])
            links.new(toon_node.outputs['BSDF'], mix_node.inputs[1]) 
            links.new(transparent_node.outputs['BSDF'], mix_node.inputs[2]) 
            
            final_shader = mix_node.outputs['Shader']
            
        # --- 最終接続 ---
        links.new(final_shader, output_node.inputs['Surface'])
        
        # 古いノードを削除
        nodes.remove(principled_node)
        
        return True

    def _find_output_node(self, nodes):
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
        objects_to_process = set()
        
        def collect_recursive(obj):
            objects_to_process.add(obj)
            for child in obj.children:
                collect_recursive(child)
        
        for obj in context.selected_objects:
            collect_recursive(obj)
            
        # 収集したオブジェクトごとにリバート処理を実行
        processed_count = 0
        for obj in objects_to_process:
            if not obj.data or not hasattr(obj.data, 'materials'):
                continue
                
            for slot in obj.material_slots:
                if slot.material:
                    if self.revert_material(slot.material):
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
        output_node = self._find_output_node(nodes)
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
            
            # InvertノードとAlphaソースを探す
            if mix_node.inputs[0].is_linked:
                invert_node = mix_node.inputs[0].links[0].from_node
                if invert_node.type == 'INVERT':
                    nodes_to_remove.append(invert_node)
                    if invert_node.inputs['Color'].is_linked:
                        # これが元のAlphaソース
                        alpha_source = invert_node.inputs['Color'].links[0].from_socket

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
        for n in nodes_to_remove:
            nodes.remove(n)
            
        return True

    def _find_output_node(self, nodes):
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
