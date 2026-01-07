
# アドオン情報
bl_info = {
    "name": "CyclesTooner",
    "author": "Antigravity",
    "version": (1, 8),
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
    operators_outline.OBJECT_OT_AddOutline,
    operators_outline.OBJECT_OT_RemoveOutline,
    ui.VIEW3D_PT_CyclesTooner,
)

def register():
    """
    アドオン有効化時の登録処理
    """
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """
    アドオン無効化時の解除処理
    """
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
