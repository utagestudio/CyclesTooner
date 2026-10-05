import sys
import urllib.parse

import bpy

OUTLINE_MATERIAL_NAME = "Toon_Outline"
OUTLINE_MATERIAL_PROPERTY = "cyclestooner_outline_material"
CONTACT_FORM_URL_JA = "https://tally.so/r/kdVdDR"
CONTACT_FORM_URL_EN = "https://tally.so/r/KYqY78"
CONTACT_FORM_PRODUCT = "CyclesTooner"


def get_addon_version_string():
    # ui is imported by the package, so read the version when it is needed.
    module = sys.modules.get(__package__) if __package__ else sys.modules.get("__main__")
    return getattr(module, "ADDON_VERSION_STRING", "")


def build_contact_form_url():
    """Return the contact form URL for Blender's language with the product and version filled in."""
    locale = bpy.app.translations.locale or ""
    base_url = CONTACT_FORM_URL_JA if locale.startswith("ja") else CONTACT_FORM_URL_EN
    params = {"product": CONTACT_FORM_PRODUCT}
    version = get_addon_version_string()
    if version:
        params["version"] = version
    return f"{base_url}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"


def is_outline_material(mat):
    return bool(mat and (mat.get(OUTLINE_MATERIAL_PROPERTY) or mat.name == OUTLINE_MATERIAL_NAME))


class WM_OT_CyclesToonerContact(bpy.types.Operator):
    """お問い合わせフォームをブラウザで開きます。"""
    bl_idname = "wm.cyclestooner_contact"
    bl_label = "Contact"
    bl_description = "Open the contact form in a web browser to send a bug report, request, or question"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.url_open(url=build_contact_form_url())
        return {'FINISHED'}


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
        column.prop(context.scene, "cyclestooner_batch_smooth", text="Smooth")
        row = column.row()
        op = row.operator("object.set_toon_smooth", text="Apply Smooth")
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
            box.prop(active_mat, "cyclestooner_opacity", text="Opacity")
            box.prop(active_mat, "cyclestooner_smooth", text="Smooth")
            box.prop(active_mat, "cyclestooner_no_shadow", text="No Shadow")
            box.prop(active_mat, "cyclestooner_emission", text="Emission")
            if active_mat.cyclestooner_emission:
                box.prop(active_mat, "cyclestooner_emission_factor", text="Emission Factor")
        
        column.separator()
        
        # オペレーター実行ボタンを配置 (アウトライン追加)
        row = column.row()
        row.scale_y = 1.2
        row.operator("object.add_toon_outline", text="Add Outline")

        # オペレーター実行ボタンを配置 (アウトライン更新)
        row = column.row()
        row.operator("object.refresh_toon_outline", text="Refresh Outline")
        
        # オペレーター実行ボタンを配置 (アウトライン削除)
        row = column.row()
        row.operator("object.remove_toon_outline", text="Remove Outline")

        column.prop(context.scene, "cyclestooner_outline_color", text="Outline Color")
        row = column.row()
        op = row.operator("object.set_toon_outline_color", text="Apply Outline Color")
        op.color = context.scene.cyclestooner_outline_color

        column.prop(context.scene, "cyclestooner_outline_thickness", text="Outline Thickness")
        row = column.row()
        op = row.operator("object.set_toon_outline_thickness", text="Apply Outline Thickness")
        op.thickness = context.scene.cyclestooner_outline_thickness

        column.separator()

        # お問い合わせフォームを開く
        row = column.row()
        row.operator("wm.cyclestooner_contact", text="Contact", icon='URL')
