import bpy

class VIEW3D_PT_CyclesTooner(bpy.types.Panel):
    """
    3Dビューポートのサイドバーに追加されるパネルの定義
    """
    # パネルの上部に表示されるラベル
    bl_label = "CyclesTooner"
    # クラスID（一意である必要がある）
    bl_idname = "VIEW3D_PT_cyclestooner"
    # 表示されるスペース（3Dビューポート）
    bl_space_type = 'VIEW_3D'
    # リージョン（UI、サイドバー）
    bl_region_type = 'UI'
    # サイドバー内のタブ名（'Tool'タブに追加）
    bl_category = 'Tool'

    def draw(self, context):
        """
        パネルのUI描画処理
        """
        layout = self.layout
        column = layout.column()
        
        # オペレーター実行ボタンを配置 (変換)
        row = column.row()
        row.scale_y = 1.5
        row.operator("object.to_toon_converter", text="Convert")
        
        # オペレーター実行ボタンを配置 (リバート)
        row = column.row()
        row.operator("object.to_toon_reverter", text="Revert")

        column.separator()

        # 透明度の一括適用
        column.prop(context.scene, "cyclestooner_batch_opacity", text="Opacity")
        row = column.row()
        op = row.operator("object.set_toon_opacity", text="Apply Opacity")
        op.opacity = context.scene.cyclestooner_batch_opacity

        active_mat = context.object.active_material if context.object else None
        if (
            active_mat
            and active_mat.name != "Toon_Outline"
            and active_mat.use_nodes
            and active_mat.node_tree
            and active_mat.node_tree.nodes.get("CyclesTooner_Opacity")
        ):
            box = column.box()
            box.label(text=f"Material: {active_mat.name}")
            box.prop(active_mat, "cyclestooner_opacity", text="Opacity")
        
        column.separator()
        
        # オペレーター実行ボタンを配置 (アウトライン追加)
        row = column.row()
        row.scale_y = 1.2
        row.operator("object.add_toon_outline", text="Add Outline")
        
        # オペレーター実行ボタンを配置 (アウトライン削除)
        row = column.row()
        row.operator("object.remove_toon_outline", text="Remove Outline")
