import bpy

OUTLINE_MATERIAL_NAME = "Toon_Outline"
OUTLINE_MATERIAL_PROPERTY = "cyclestooner_outline_material"


def is_outline_material(mat):
    return bool(mat and (mat.get(OUTLINE_MATERIAL_PROPERTY) or mat.name == OUTLINE_MATERIAL_NAME))


class VIEW3D_PT_CyclesTooner(bpy.types.Panel):
    """
    3Dビューポートのサイドバーに追加されるパネルの定義
    """
    # パネルの上部に表示されるラベル
    bl_label = "CyclesTooner"
    bl_description = "Convert toon materials to Toon BSDF and manage outlines for Cycles"
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
        row.operator("object.to_toon_converter", text="Convert", translate=False)
        
        # オペレーター実行ボタンを配置 (リバート)
        row = column.row()
        row.operator("object.to_toon_reverter", text="Revert", translate=False)

        column.separator()

        # 透明度の一括適用
        column.prop(context.scene, "cyclestooner_batch_opacity", text="Opacity", translate=False)
        row = column.row()
        op = row.operator("object.set_toon_opacity", text="Apply Opacity", translate=False)
        op.opacity = context.scene.cyclestooner_batch_opacity
        column.prop(context.scene, "cyclestooner_batch_smooth", text="Smooth", translate=False)
        row = column.row()
        op = row.operator("object.set_toon_smooth", text="Apply Smooth", translate=False)
        op.smooth = context.scene.cyclestooner_batch_smooth

        active_mat = context.object.active_material if context.object else None
        if (
            active_mat
            and not is_outline_material(active_mat)
            and active_mat.use_nodes
            and active_mat.node_tree
            and active_mat.node_tree.nodes.get("CyclesTooner_Opacity")
        ):
            box = column.box()
            box.label(text=f"Material: {active_mat.name}")
            box.prop(active_mat, "cyclestooner_opacity", text="Opacity", translate=False)
            box.prop(active_mat, "cyclestooner_smooth", text="Smooth", translate=False)
            box.prop(active_mat, "cyclestooner_no_shadow", text="No Shadow", translate=False)
            box.prop(active_mat, "cyclestooner_emission", text="Emission", translate=False)
            if active_mat.cyclestooner_emission:
                box.prop(active_mat, "cyclestooner_emission_factor", text="Emission Factor", translate=False)
        
        column.separator()
        
        # オペレーター実行ボタンを配置 (アウトライン追加)
        row = column.row()
        row.scale_y = 1.2
        row.operator("object.add_toon_outline", text="Add Outline", translate=False)

        # オペレーター実行ボタンを配置 (アウトライン更新)
        row = column.row()
        row.operator("object.refresh_toon_outline", text="Refresh Outline", translate=False)
        
        # オペレーター実行ボタンを配置 (アウトライン削除)
        row = column.row()
        row.operator("object.remove_toon_outline", text="Remove Outline", translate=False)

        column.prop(context.scene, "cyclestooner_outline_color", text="Outline Color", translate=False)
        row = column.row()
        op = row.operator("object.set_toon_outline_color", text="Apply Outline Color", translate=False)
        op.color = context.scene.cyclestooner_outline_color

        column.prop(context.scene, "cyclestooner_outline_thickness", text="Outline Thickness", translate=False)
        row = column.row()
        op = row.operator("object.set_toon_outline_thickness", text="Apply Outline Thickness", translate=False)
        op.thickness = context.scene.cyclestooner_outline_thickness
