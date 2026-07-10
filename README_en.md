# CyclesTooner - Blender Toon Shader Assistant

CyclesTooner is a Blender add-on designed to streamline the process of creating toon (cel-shaded) looks.  
It provides features to batch convert Principled BSDF materials to Toon BSDF and automatically generate outlines using the "inverted hull" (backfacing) method, optimized for the Cycles renderer.

## Features

### 1. Material Converter
Automatically converts materials for selected objects (and all their children recursively).

*   **Convert**:
    *   Replaces `Principled BSDF` with `Toon BSDF` (Size: 0.8).
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

### 2. Outline Generator
Generates outline meshes using the "inverted hull" method via Geometry Nodes, ideal for toon shading in Cycles.

*   **Add Outline**:
    *   Creates an outline object that references all meshes within the selected **Collection**.
    *   Uses **Geometry Nodes** to slightly extrude the model along its normals and display backfaces.
    *   **Thickness Control**:
        *   Control thickness per vertex using Vertex Weights (Default input: "Weight" set to 0.5).
        *   Adjust global thickness multiplier via the Modifier settings (`Value`).
    *   Automatically disables viewport selection (Selectable: OFF) and Cycles Ray Visibility (Diffuse/Shadow: OFF).
*   **Remove Outline**:
    *   Deletes the generated outline mesh.
    *   Automatically cleans up unused Geometry Node groups and materials created by the add-on.

## Installation

1.  Download this repository as a ZIP file.
2.  Open Blender and go to `Edit` > `Preferences` > `Add-ons`.
3.  Click `Install` and select the downloaded ZIP file.
4.  Check the box for **"Material: CyclesTooner"** to enable it.

## Usage

The **CyclesTooner** panel is located in the **Tool** tab of the 3D Viewport Sidebar (press N).

### Converting Materials
1.  Select the object(s) you want to convert.
2.  Click the **Convert** button to apply toon shading.
3.  Adjust the **Opacity** slider and click **Apply Opacity** to apply transparency to the selected toon materials in bulk.
4.  If the active material has been converted by CyclesTooner, use the **Material** opacity field for per-material adjustment.
5.  Click the **Revert** button to restore the original materials.

### Creating Outlines
1.  Select (make active) the **Collection** containing your target objects in the Outliner.
2.  Click the **Add Outline** button.
    *   A new object named `~_Outline` will be created in the same hierarchy.
3.  If you want to adjust the outline thickness using vertex weights, click the "Input Attribute Toggle" on the `Weight` input of the `ToonOutlineGN` modifier, and enter the name of the vertex group containing the weight information.
4.  To remove it, select either the outline object or the original collection and click **Remove Outline**.

## Requirements
*   Blender 5.0 (Recommended) / 3.0+
*   Recommended Renderer: **Cycles** (The outline feature is optimized for Cycles)

## License
[MIT License](LICENSE)
