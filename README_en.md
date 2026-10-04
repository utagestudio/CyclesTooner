# CyclesTooner

English | [日本語](README.md)

CyclesTooner is a Blender add-on that **lets avatar models set up with EEVEE-oriented shaders, such as VRM and MMD avatars, render with a toon look in Cycles**.

The MToon, VRToon, and UnityToon shaders build their shading with the EEVEE-only `Shader to RGB` node, so they do not look as intended when rendered in Cycles. MMD (MMDShaderDev) materials are also designed for EEVEE display. CyclesTooner replaces these materials with Blender's built-in **Toon BSDF**, carrying over textures, colors, normals, and transparency where possible. It also generates inverted-hull outlines with Geometry Nodes that work in Cycles.

Use it when you want toon characters in scenes that rely on Cycles reflections, refraction, volumetrics, or fisheye lenses.

## What It Does

- **Material conversion**: Converts MToon (VRM Add-on for Blender), MMDShaderDev (MMD Tools), VRToon (VRToon Shader Manager), UnityToon and Unlit (Unitypackage Importer), and Principled BSDF materials to Toon BSDF.
- **Outline generation**: Creates an inverted-hull outline around the whole model. Vertex weights control the thickness of each part.
- **Batch adjustment**: Changes Opacity and Smooth (softness of the shading boundary) across converted materials at once.

## Requirements

- Blender 5.2 LTS (recommended) / 4.5 LTS or later
- Renderer: Cycles (outlines are tuned for Cycles)

## Installation

### From the Extension Repository (Recommended)

Once the repository is registered, Blender detects new versions at startup and you can update in place.

1. In Blender, open `Edit` > `Preferences` > `Get Extensions`.
2. From the `Repositories` dropdown in the top right, choose `[+]` > `Add Remote Repository`.
3. Enter the following URL:
   ```
   https://utagestudio.github.io/CyclesTooner/index.json
   ```
4. Enable `Check for Updates on Startup` and add the repository.
5. Click `Install` next to **CyclesTooner** in the list.

### From a ZIP File

Use this method when you cannot register the repository, for example on an offline machine.

1. Download the `cycles_tooner-<version>.zip` named in the `archive_url` field of [index.json](https://utagestudio.github.io/CyclesTooner/index.json). Its URL is the file name appended to `https://utagestudio.github.io/CyclesTooner/`.
2. In Blender, open `Edit` > `Preferences` > `Get Extensions`.
3. From the `⌄` menu in the top right, choose `Install from Disk...` and select the downloaded ZIP.

Do not install the source code from GitHub's "Download ZIP"; it contains development files. This method does not update automatically.

## Quick Start

The **CyclesTooner** panel is in the **Tool** tab of the 3D Viewport sidebar (press `N`).

1. **Save your .blend file before converting.** (See [Before You Convert](#before-you-convert).)
2. Select the model's **root** (the topmost parent, such as an Armature or Empty) and click **Convert**. Materials on the selected object and all of its descendants are converted.
3. Select any object in the model and click **Add Outline**.
4. Render with Cycles. Adjust Smooth, Opacity, and the outline color and thickness as needed.

## Before You Convert

Convert and Add Outline modify scene data directly. Save your .blend file first if you might need the original state.

- **Convert removes the original shader.** Materials converted from MToon, MMDShaderDev, VRToon, UnityToon, or Unlit do not return to the original shader on **Revert**; they become a simplified Principled BSDF material.
- **Not every effect of the original shader is reproduced.** Shade colors, MatCap, rim lighting, specular, and emission are not reproduced by Toon BSDF. (See [Supported Shaders](#supported-shaders).)
- **Convert removes VRToon outlines.** Their thickness is saved, so clicking **Add Outline** rebuilds them as CyclesTooner outlines.
- **Add Outline changes collection membership.** Every object in the model hierarchy moves into a newly created `<root name>_Collection`.
- **The render engine switches to Cycles.** Clicking Convert while EEVEE is active changes the engine to Cycles automatically.
- Ordinary Emission nodes and other unsupported shaders are left unchanged.

## Supported Shaders

| Source | Created by | Carried over | Not reproduced |
| --- | --- | --- | --- |
| Principled BSDF | Built into Blender | Base Color (color and texture), Normal, Alpha | Metallic, roughness, specular, and similar surface properties |
| MToon | [VRM Add-on for Blender](https://vrm-addon-for-blender.info/en-us/) | Base texture color and alpha, UV transforms, Normal, Base Color, Alpha | Shade Color, MatCap, Rim, Emission, Outline |
| MMDShaderDev | [MMD Tools](https://extensions.blender.org/add-ons/mmd-tools/) | `mmd_base_tex` color and alpha, UV transforms, Normal, Diffuse Color, Alpha | Sphere textures, Toon textures |
| VRToon | [VRToon Shader Manager](https://kafuji.github.io/Sakura-Creative-Suite/en/addons/VRToon_Shader_Manager/) | Base Color (color and texture), Normal, Alpha and Material Alpha, outline thickness | Shading, specular, rim, AO, masks |
| UnityToon (v1) | [Unitypackage Importer](https://utagestudio.github.io/unitypackage_loader/) | Base Color (including texture, tint, and UV transforms), Normal, Alpha | Shadows, MatCap, rim, emission |
| Unlit | [Unitypackage Importer](https://utagestudio.github.io/unitypackage_loader/) | Color, texture, Alpha | — |

- Converted Toon BSDF nodes start with `Size: 0.8` and `Smooth: 0.2`.
- None of these add-ons are bundled with CyclesTooner. Some color and transparency values are read from each add-on's material settings, so keep the add-on that imported the model enabled while converting.
- VRToon is converted when a shader group whose name starts with `VRToon` is connected to the Material Output. UnityToon and Unlit are converted only when their setup was created by Unitypackage Importer.
- lilToon and Poiyomi, which many VRChat avatars use, cannot be converted directly. CyclesTooner converts the materials (UnityToon and Unlit) after Unitypackage Importer has imported the avatar.

## Feature Details

### Material Conversion

- **Convert**: Converts materials on the selected objects and their descendants.
  - Transparency is controlled by one shared setup that mixes Toon BSDF with Transparent BSDF through a Mix Shader. The original material's alpha (texture or value) is carried into this setup.
  - Sets the material render method to `Dithered` so that EEVEE and Material Preview display correctly. This does not affect the Cycles result.
  - Converted nodes are arranged by connection order. Disconnected nodes whose purpose cannot be determined are kept in a `CyclesTooner Preserved Nodes` frame instead of being deleted.
- **Revert**: Returns converted materials to Principled BSDF. Materials converted from anything other than Principled BSDF become a simplified Principled BSDF material, not the original shader.
- **Opacity / Apply Opacity**: Sets opacity on converted materials of the selected objects and their descendants. `1.0` is opaque and `0.0` is fully transparent.
- **Smooth / Apply Smooth**: Sets Toon BSDF Smooth for the same range. Higher values soften the shading boundary.
- **Material fields**: When the active material has been converted, change Opacity and Smooth for that material only.

### Outlines

- **Add Outline**: Uses the topmost parent of the selected object (including Empty roots) as the root and creates an outline for the whole model with this structure:

  ```text
  <root name>_Collection
  ├─ <root name> (and all descendants)
  └─ <root name>_Outline_Collection
     ├─ <root name>_Outline          … the outline object
     └─ <root name>_Outline_Source   … outline source meshes (excluded from the View Layer)
  ```

  - Only meshes that render are outline sources. Meshes disabled for rendering on the object or a collection are excluded. Meshes hidden only in the viewport are included.
  - Each model gets its own outline material, so each model can have its own outline color.
  - The outline is set as unselectable and does not appear in Cycles diffuse reflections or shadows.
- **Thickness**
  - Change the overall thickness with **Outline Thickness** and **Apply Outline Thickness** (default `0.002`), or with `Thickness` on the `ToonOutlineGN` modifier.
  - Each source mesh receives a `CT_Outline` vertex group with every vertex weighted `0.5`. Paint the weights to vary thickness by area.
  - An existing `CT_Outline` group keeps its weights.
  - Models converted from VRToon use the thickness and weights saved during Convert.
- **Outline Color / Apply Outline Color**: Changes the outline color of the selected model.
- **Refresh Outline**: Rebuilds the outline sources after you show or hide model parts. Select an object in the model or the outline object first. Color and thickness settings are kept.
- **Remove Outline**: Deletes the outline object, its source collection, and outline data that is no longer used. Select an object in the model or the outline object first.

## Troubleshooting

Messages and tooltips follow Blender's language setting and appear in English or Japanese.

| Symptom | Solution |
| --- | --- |
| Some materials do not change after Convert | Only the selected objects and their descendants are converted, so select the model root. Unsupported shaders are not converted. (See [Supported Shaders](#supported-shaders).) |
| "An outline already exists for this root object." | The outline already exists. Update its sources with **Refresh Outline**, or delete it with **Remove Outline** and create it again. |
| "No render-visible mesh was found for the outline." | The model hierarchy has no mesh that renders. Check the render visibility of the objects and collections. |
| The outline remains after hiding a part | Click **Refresh Outline**. |
| A VRToon outline disappeared after Convert | This is expected. Click **Add Outline** to rebuild it with the saved thickness. |
| Revert does not restore the original look | Conversions from shaders other than Principled BSDF cannot be restored. Use the .blend file you saved before converting. |

## Contact

Bug reports, requests, and questions can be sent through the [contact form](https://tally.so/r/KYqY78?product=CyclesTooner).
If you have a GitHub account, [Issues](https://github.com/utagestudio/CyclesTooner/issues) works as well.

## For Developers

- Add-on behavior specification: [docs/behavior.md](docs/behavior.md)
- Versioning, branch, commit, and release workflow: [VERSIONING.md](VERSIONING.md)

## License

[GPL-3.0-or-later](LICENSE)
