# CyclesTooner - Blender Toon Shader Assistant

CyclesTooner is a Blender add-on that streamlines toon (cel-shaded) rendering by simply converting Principled BSDF, MMD (mmd_shader), and VRM (MToon) shaders into a Toon BSDF usable in Cycles.  
It also includes automatic outline generation using the "inverted hull" (backfacing) method, which renders cleanly in the Cycles renderer.

## Features

### 1. Material Converter
Automatically converts materials for selected objects (and all their children recursively).

*   **Convert**:
    *   Replaces `Principled BSDF` with `Toon BSDF` (Size: 0.8 / Smooth: 0.2).
    *   Directly converts MMD Tools `MMDShaderDev` / `mmd_shader` materials to `Toon BSDF`.
    *   Directly converts VRM Add-on for Blender `MToon` materials to `Toon BSDF`.
    *   Preserves `Base Color` and `Normal` connections.
    *   Automatically adds opacity control nodes (Mix Shader + Transparent BSDF).
    *   If there is an `Alpha` connection, both the Alpha input and Opacity setting are applied.
    *   Automatically switches the render engine to **Cycles** if EEVEE is currently selected.
*   **Revert**:
    *   Restores materials converted by CyclesTooner back to `Principled BSDF`.
*   **Opacity**:
    *   Applies opacity in bulk to toon materials on selected objects and their children from the sidebar slider.
    *   Allows per-material opacity adjustment when the active object's material has been converted by CyclesTooner.
    *   `1.0` is fully opaque, and `0.0` is fully transparent.
*   **Smooth**:
    *   Applies Toon Smooth in bulk to toon materials on selected objects and their children from the sidebar slider.
    *   Allows per-material Smooth adjustment when the active object's material has been converted by CyclesTooner.

### 2. Outline Generator
Generates outline meshes using the "inverted hull" method via Geometry Nodes, ideal for toon shading in Cycles.

*   **Add Outline**:
    *   Creates an outline object from meshes under the selected object's topmost parent, including Empty roots.
    *   Creates a root management collection containing every object under the root and the outline management collection.
    *   Uses **Geometry Nodes** to slightly extrude the model along its normals and display backfaces.
    *   Hidden mesh objects are excluded from the outline source.
    *   **Thickness Control**:
        *   Control thickness per vertex using Vertex Weights (Default input: "Weight" set to 0.5).
        *   Adjust global thickness multiplier via the Modifier settings (`Value`).
    *   Automatically disables viewport selection (Selectable: OFF) and Cycles Ray Visibility (Diffuse/Shadow: OFF).
*   **Remove Outline**:
    *   Deletes the generated outline mesh.
    *   Automatically cleans up unused Geometry Node groups and materials created by the add-on.
*   **Refresh Outline**:
    *   Updates an existing outline source to match the current visibility state only while a model part or generated outline is selected.

## Installation

### From the Extension Repository (Recommended, Blender 4.2+)

Registering the remote repository lets Blender detect updates on startup so you can update with one click.

1.  Open Blender and go to `Edit` > `Preferences` > `Get Extensions`.
2.  From the `Repositories` dropdown in the top right, choose `[+]` > `Add Remote Repository`.
3.  Enter the following URL:
    ```
    https://utagestudio.github.io/CyclesTooner/index.json
    ```
4.  Enable **Check for Updates on Startup** and add the repository.
5.  Find **CyclesTooner** in the extension list and click `Install`.
6.  From now on, new releases are detected when Blender starts, and you can update from the `Get Extensions` page.

### From a ZIP file (Blender 4.1 and earlier)

1.  Download this repository as a ZIP file.
2.  Open Blender and go to `Edit` > `Preferences` > `Add-ons`.
3.  Click `Install` and select the downloaded ZIP file.
4.  Check the box for **"Material: CyclesTooner"** to enable it.

## Usage

The **CyclesTooner** panel is located in the **Tool** tab of the 3D Viewport Sidebar (press N).

### Converting Materials
1.  Select the object(s) you want to convert.
2.  Click the **Convert** button to apply toon shading.
3.  Adjust the **Opacity** / **Smooth** sliders and click **Apply Opacity** / **Apply Smooth** to update selected toon materials in bulk.
4.  If the active material has been converted by CyclesTooner, use the **Material** fields for per-material Opacity/Smooth adjustment.
5.  Click the **Revert** button to restore the original materials.

#### Direct MMDShaderDev Conversion
Materials loaded by MMD Tools with `mmd_shader` can be converted directly with **Convert**.

CyclesTooner preserves `mmd_base_tex` image color/alpha and MMD Diffuse Color where possible. MMD material Alpha is folded into the initial **Opacity** value. The conversion removes `MMDShaderDev` nodes, so **Revert** restores a simplified `Principled BSDF` material rather than the original MMDShaderDev node setup. Exact Sphere/Toon texture compositing is not preserved.

#### Direct MToon Conversion
Materials loaded by VRM Add-on for Blender with `MToon` can be converted directly with **Convert**.

CyclesTooner preserves base texture color/alpha and MToon Base Color where possible. MToon Alpha is folded into the initial **Opacity** value. The conversion removes `MToon` nodes, so **Revert** restores a simplified `Principled BSDF` material rather than the original MToon node setup. Exact MToon Shade Color, MatCap, Rim, Emission, and Outline effects are not preserved.

### Creating Outlines
1.  Select an object inside the model you want to outline.
2.  Click the **Add Outline** button.
    *   The selected object's topmost parent is used as the outline root, and only that hierarchy is targeted.
    *   A collection named `~_Collection` is created beside the root, and every object under the root is moved into it.
    *   A collection named `~_Outline_Collection` is created inside `~_Collection`.
    *   The generated `~_Outline` object and internal `~_Outline_Source` collection are created inside `~_Outline_Collection`.
3.  If you show or hide model parts, select a target part or the generated outline and click **Refresh Outline** to update the outline source.
4.  If you want to adjust the outline thickness using vertex weights, click the "Input Attribute Toggle" on the `Weight` input of the `ToonOutlineGN` modifier, and enter the name of the vertex group containing the weight information.
5.  To remove it, select either the outline object or the original collection and click **Remove Outline**.

## Requirements
*   Blender 5.0 (Recommended) / 3.0+
*   Recommended Renderer: **Cycles** (The outline feature is optimized for Cycles)

## License
[GPL-3.0-or-later](LICENSE)
