import bpy


# English is the source language. Keep every user-facing message, tooltip, and
# property description here with its Japanese translation.
JAPANESE = {
    # Material conversion reports
    "Switched the render engine to Cycles.": "レンダーエンジンをCyclesに切り替えました。",
    "Converted materials on {count} object(s) to Toon BSDF.": "{count} 個のオブジェクトのマテリアルを Toon 化しました。",
    "Saved outline data from {count} VRToon outline(s). Use Add Outline to recreate them.":
        "VRToonアウトライン情報を{count}個退避しました。Add Outlineで再作成できます。",
    "Reverted materials on {count} object(s).": "{count} 個のオブジェクトのマテリアルを元に戻しました。",
    "Applied opacity to {count} material(s).": "{count} 個のマテリアルに透明度を適用しました。",
    "Applied Smooth to {count} material(s).": "{count} 個のマテリアルにSmoothを適用しました。",

    # Outline reports
    "Select an object to outline.": "アウトライン対象のオブジェクトを選択してください。",
    "An outline already exists for this root object. Use Refresh Outline instead.":
        "このルートオブジェクトのアウトラインは既に存在します。Refresh Outlineを使用してください。",
    "No render-visible mesh was found for the outline.": "アウトライン対象のレンダー対象メッシュが見つかりませんでした。",
    "Could not set the outline Collection input.": "アウトラインのCollection入力を設定できませんでした。",
    "Created an outline for root object '{name}' ({count} mesh(es)).":
        "ルートオブジェクト '{name}' のアウトラインを作成しました。({count} メッシュ)",
    "Created an outline for root object '{name}' ({count} mesh(es), VRToon migration {migrated}/{removed}).":
        "ルートオブジェクト '{name}' のアウトラインを作成しました。({count} メッシュ, VRToon移行 {migrated}/{removed})",
    "No outline was found for the selected model.": "選択中のモデルに対応するアウトラインが見つかりませんでした。",
    "The outline material was not found.": "アウトライン用マテリアルが見つかりませんでした。",
    "Changed the outline color.": "アウトライン色を変更しました。",
    "Could not update the outline Thickness input.": "アウトラインのThickness入力を更新できませんでした。",
    "Changed the outline thickness.": "アウトラインの太さを変更しました。",
    "No collection to refresh was found.": "更新対象のコレクションが見つかりませんでした。",
    "No outline to refresh was found. Run Add Outline first.":
        "更新対象のアウトラインが見つかりませんでした。先にAdd Outlineを実行してください。",
    "The outline Geometry Nodes modifier was not found.": "アウトラインのGeometry Nodesモディファイアが見つかりませんでした。",
    "The outline Collection input was not found.": "アウトラインのCollection入力が見つかりませんでした。",
    "No render-visible mesh was found for the outline. The existing sources were kept.":
        "アウトライン対象のレンダー対象メッシュが見つかりませんでした。既存の対象は維持しました。",
    "Could not update the outline Collection input.": "アウトラインのCollection入力を更新できませんでした。",
    "Refreshed the outline sources for collection '{name}' ({count} mesh(es)).":
        "コレクション '{name}' のアウトライン対象を更新しました。({count} メッシュ)",
    "No outline to remove was found.": "削除対象のアウトラインが見つかりませんでした。",
    "Removed the outline (cleanup: Container={containers}, Src={sources}, Mesh={meshes}, NG={groups}, Mat={materials}).":
        "アウトラインを削除しました。(Cleanup: Container={containers}, Src={sources}, Mesh={meshes}, NG={groups}, Mat={materials})",

    # Tooltips (bl_description)
    "Convert toon materials to Toon BSDF and manage outlines for Cycles":
        "トゥーン用のマテリアルをToon BSDFに変換し、Cycles用のアウトラインを管理します",
    "Convert the materials of the selected objects and their descendants to Toon BSDF for Cycles":
        "選択したオブジェクトとその子孫のマテリアルを、Cycles用のToon BSDFに変換します",
    "Restore converted materials to Principled BSDF. Materials converted from other shaders become a simplified Principled BSDF":
        "変換したマテリアルをPrincipled BSDFに戻します。Principled BSDF以外から変換したマテリアルは、簡易的なPrincipled BSDFになります",
    "Apply the opacity to the converted materials of the selected objects and their descendants":
        "選択したオブジェクトとその子孫の変換済みマテリアルに、不透明度をまとめて適用します",
    "Apply the Smooth value to the converted materials of the selected objects and their descendants":
        "選択したオブジェクトとその子孫の変換済みマテリアルに、Smoothの値をまとめて適用します",
    "Create an inverted-hull outline for the model that contains the selected object. Intended for models converted by CyclesTooner":
        "選択したオブジェクトを含むモデルに、背面法のアウトラインを作成します。CyclesTooner で変換済みのモデル向けの機能です",
    "Apply the outline color to the selected model's outline": "選択したモデルのアウトラインに色を適用します",
    "Apply the base thickness to the selected model's outline": "選択したモデルのアウトラインに基本の太さを適用します",
    "Rebuild the outline sources from the model's current render visibility":
        "モデルの現在のレンダー表示状態に合わせて、アウトラインの対象を作り直します",
    "Remove the selected model's outline and its unused data":
        "選択したモデルのアウトラインと、使われなくなったデータを削除します",

    # Property descriptions
    "Opacity applied to selected toon materials": "選択したToonマテリアルに適用する不透明度",
    "Smooth value applied to selected toon materials": "選択したToonマテリアルに適用するSmoothの値",
    "Color applied to the selected model's outline": "選択したモデルのアウトラインに適用する色",
    "Base outline thickness in Blender units": "アウトラインの基本の太さ（Blenderの単位）",
    "Opacity for this CyclesTooner material": "このCyclesToonerマテリアルの不透明度",
    "Smooth value for this CyclesTooner material": "このCyclesToonerマテリアルのSmoothの値",
    "Stop this CyclesTooner material from casting shadows in Cycles":
        "このCyclesToonerマテリアルがCyclesで影を落とさないようにします",
    "Mix an Emission shader into this CyclesTooner material so that it keeps its color in shade":
        "このCyclesToonerマテリアルにEmissionを混ぜて、陰の中でも色が沈まないようにします",
    "How much of the Emission shader is mixed in. 0 keeps the Toon shading and 1 shows the unshaded color":
        "Emissionを混ぜる割合。0でToonの陰影のまま、1で陰影のない色になります",
}

TRANSLATIONS = {
    "ja_JP": {("*", source): japanese for source, japanese in JAPANESE.items()},
}


def report_message(message, **values):
    """Translate a report message, then fill in its values."""
    return bpy.app.translations.pgettext_rpt(message).format(**values)


def register(module_name):
    bpy.app.translations.register(module_name, TRANSLATIONS)


def unregister(module_name):
    bpy.app.translations.unregister(module_name)
