
# Version target and development identifier. The manifest stores the complete
# SemVer string; Blender's bl_info accepts only the integer core tuple.
ADDON_VERSION = (1, 28, 1)
ADDON_VERSION_PRERELEASE = "dev.3"
ADDON_VERSION_STRING = ".".join(map(str, ADDON_VERSION))
if ADDON_VERSION_PRERELEASE:
    ADDON_VERSION_STRING = f"{ADDON_VERSION_STRING}-{ADDON_VERSION_PRERELEASE}"

# アドオン情報
bl_info = {
    "name": "CyclesTooner",
    "author": "utagestudio",
    # Keep the core version synchronized with ADDON_VERSION_STRING and
    # blender_manifest.toml. See VERSIONING.md for the release workflow.
    "version": ADDON_VERSION,
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Convert EEVEE toon avatars to Toon BSDF for Cycles",
    "category": "Material",
}

# Blender re-executes this file on Reload Scripts with the previous namespace
# still in place, so "bpy" is already defined on a reload.
_needs_reload = "bpy" in locals()

import bpy
from . import (
    translations,
    operators_converter,
    operators_outline,
    ui,
)

# translations is reloaded first because the operator modules import from it.
if _needs_reload:
    import importlib
    translations = importlib.reload(translations)
    operators_converter = importlib.reload(operators_converter)
    operators_outline = importlib.reload(operators_outline)
    ui = importlib.reload(ui)

# 登録対象のクラスリスト
classes = (
    operators_converter.OBJECT_OT_ToonConverter,
    operators_converter.OBJECT_OT_ToonReverter,
    operators_converter.OBJECT_OT_SetToonOpacity,
    operators_converter.OBJECT_OT_SetToonSmooth,
    operators_outline.OBJECT_OT_SetOutlineColor,
    operators_outline.OBJECT_OT_SetOutlineThickness,
    operators_outline.OBJECT_OT_AddOutline,
    operators_outline.OBJECT_OT_RefreshOutline,
    operators_outline.OBJECT_OT_RemoveOutline,
    ui.WM_OT_CyclesToonerContact,
    ui.VIEW3D_PT_CyclesTooner,
)

def register():
    """
    アドオン有効化時の登録処理
    """
    translations.register(__name__)

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
    bpy.types.Scene.cyclestooner_outline_color = bpy.props.FloatVectorProperty(
        name="Outline Color",
        description="Color applied to the selected model's outline",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=operators_outline.DEFAULT_OUTLINE_COLOR,
    )
    bpy.types.Scene.cyclestooner_outline_thickness = bpy.props.FloatProperty(
        name="Outline Thickness",
        description="Base outline thickness in Blender units",
        subtype='DISTANCE',
        min=0.0,
        soft_max=0.1,
        precision=4,
        default=operators_outline.DEFAULT_OUTLINE_THICKNESS,
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
    bpy.types.Material.cyclestooner_no_shadow = bpy.props.BoolProperty(
        name="No Shadow",
        description="Stop this CyclesTooner material from casting shadows in Cycles",
        default=False,
        update=operators_converter.update_material_no_shadow_property,
    )
    bpy.types.Material.cyclestooner_emission = bpy.props.BoolProperty(
        name="Emission",
        description="Mix an Emission shader into this CyclesTooner material so that it keeps its color in shade",
        default=False,
        update=operators_converter.update_material_emission_property,
    )
    bpy.types.Material.cyclestooner_emission_factor = bpy.props.FloatProperty(
        name="Emission Factor",
        description="How much of the Emission shader is mixed in. 0 keeps the Toon shading and 1 shows the unshaded color",
        min=0.0,
        max=1.0,
        default=operators_converter.DEFAULT_EMISSION_FACTOR,
        subtype='FACTOR',
        update=operators_converter.update_material_emission_factor_property,
    )

def unregister():
    """
    アドオン無効化時の解除処理
    """
    if hasattr(bpy.types.Material, "cyclestooner_opacity"):
        del bpy.types.Material.cyclestooner_opacity
    if hasattr(bpy.types.Material, "cyclestooner_smooth"):
        del bpy.types.Material.cyclestooner_smooth
    if hasattr(bpy.types.Material, "cyclestooner_no_shadow"):
        del bpy.types.Material.cyclestooner_no_shadow
    if hasattr(bpy.types.Material, "cyclestooner_emission"):
        del bpy.types.Material.cyclestooner_emission
    if hasattr(bpy.types.Material, "cyclestooner_emission_factor"):
        del bpy.types.Material.cyclestooner_emission_factor
    if hasattr(bpy.types.Scene, "cyclestooner_batch_opacity"):
        del bpy.types.Scene.cyclestooner_batch_opacity
    if hasattr(bpy.types.Scene, "cyclestooner_batch_smooth"):
        del bpy.types.Scene.cyclestooner_batch_smooth
    if hasattr(bpy.types.Scene, "cyclestooner_outline_color"):
        del bpy.types.Scene.cyclestooner_outline_color
    if hasattr(bpy.types.Scene, "cyclestooner_outline_thickness"):
        del bpy.types.Scene.cyclestooner_outline_thickness

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    translations.unregister(__name__)

if __name__ == "__main__":
    register()
