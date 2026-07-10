
# アドオン情報
bl_info = {
    "name": "CyclesTooner",
    "author": "Codex",
    # Version format: (major, minor, dev). Increment dev for uncommitted changes,
    # then increment minor and reset dev to 0 when committing a completed change.
    # Keep in sync with "version" in blender_manifest.toml (used by Blender 4.2+ extensions).
    "version": (1, 16, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Convert Principled BSDF to Toon BSDF",
    "category": "Material",
}

import bpy
import sys
import importlib

# サブモジュールの名前リスト (New structure)
modules_names = ['operators_converter', 'operators_outline', 'ui']

# サブモジュールのリロードとインポート
# パッケージ名が解決できる場合（正規のアドオンとして読み込まれた場合）
if __package__:
    for name in modules_names:
        full_name = f"{__package__}.{name}"
        if full_name in sys.modules:
            importlib.reload(sys.modules[full_name])
            
    from . import operators_converter
    from . import operators_outline
    from . import ui

# パッケージとして解決できない場合（テキストエディタで直接実行した場合など）
else:
    import operators_converter
    import operators_outline
    import ui
    importlib.reload(operators_converter)
    importlib.reload(operators_outline)
    importlib.reload(ui)

# 登録対象のクラスリスト
classes = (
    operators_converter.OBJECT_OT_ToonConverter,
    operators_converter.OBJECT_OT_ToonReverter,
    operators_converter.OBJECT_OT_SetToonOpacity,
    operators_converter.OBJECT_OT_SetToonSmooth,
    operators_outline.OBJECT_OT_AddOutline,
    operators_outline.OBJECT_OT_RefreshOutline,
    operators_outline.OBJECT_OT_RemoveOutline,
    ui.VIEW3D_PT_CyclesTooner,
)

def register():
    """
    アドオン有効化時の登録処理
    """
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.cyclestooner_batch_opacity = bpy.props.FloatProperty(
        name="Opacity",
        description="Opacity applied to selected toon materials",
        min=0.0,
        max=1.0,
        default=1.0,
        subtype='FACTOR',
    )
    bpy.types.Scene.cyclestooner_batch_smooth = bpy.props.FloatProperty(
        name="Smooth",
        description="Smooth value applied to selected toon materials",
        min=0.0,
        max=1.0,
        default=operators_converter.DEFAULT_TOON_SMOOTH,
        subtype='FACTOR',
    )
    bpy.types.Material.cyclestooner_opacity = bpy.props.FloatProperty(
        name="Opacity",
        description="Opacity for this CyclesTooner material",
        min=0.0,
        max=1.0,
        default=1.0,
        subtype='FACTOR',
        update=operators_converter.update_material_opacity_property,
    )
    bpy.types.Material.cyclestooner_smooth = bpy.props.FloatProperty(
        name="Smooth",
        description="Smooth value for this CyclesTooner material",
        min=0.0,
        max=1.0,
        default=operators_converter.DEFAULT_TOON_SMOOTH,
        subtype='FACTOR',
        update=operators_converter.update_material_smooth_property,
    )

def unregister():
    """
    アドオン無効化時の解除処理
    """
    if hasattr(bpy.types.Material, "cyclestooner_opacity"):
        del bpy.types.Material.cyclestooner_opacity
    if hasattr(bpy.types.Material, "cyclestooner_smooth"):
        del bpy.types.Material.cyclestooner_smooth
    if hasattr(bpy.types.Scene, "cyclestooner_batch_opacity"):
        del bpy.types.Scene.cyclestooner_batch_opacity
    if hasattr(bpy.types.Scene, "cyclestooner_batch_smooth"):
        del bpy.types.Scene.cyclestooner_batch_smooth

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
