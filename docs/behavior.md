# CyclesTooner Behavior Specification

This document is the canonical specification of CyclesTooner's add-on behavior. Keep it synchronized with the code: a change that alters any rule here must update this file on the same branch.

User-facing explanations belong in `README.md`, `README_en.md`, and the GitHub Pages site. This file records the invariants that implementation and review must preserve.

## Material Conversion

### Common Rules

- Toon BSDF `Size` default is `0.8`, and `Smooth` default is `0.2`.
- Principled BSDF conversion should preserve a linked `Base Color` source. When `Base Color` is unlinked, copy its configured socket color to the Toon BSDF.
- Convert switches the scene render engine to Cycles when EEVEE is active.

### Opacity and Transparency

- Opacity control is unified through the CyclesTooner opacity flow; do not create a separate MMD/MToon/VRToon/UnityToon alpha flow.
- The flow is `Toon BSDF` and `Transparent BSDF` combined by the `CyclesTooner_OpacityMix` Mix Shader. The `CyclesTooner_AlphaOpacity` Math node multiplies the source alpha by the `CyclesTooner_Opacity` value, and `CyclesTooner_Transparency` inverts the result to drive the mix.
- Create `CyclesTooner_AlphaOpacity` in every converted material, including materials without a linked source alpha. Its first input stays unlinked at `1.0` in that case, so the result equals the Opacity value. Never overwrite the first input's value or link on an existing node; users connect their own alpha source there.
- Preserve a configured, unlinked source alpha value as the initial Opacity. An existing non-default material Opacity takes precedence.
- Set converted materials to the `DITHERED` surface render method during conversion and every opacity update. `BLENDED` does not sort faces within a mesh in EEVEE and makes nearly opaque materials look inside out in Material Preview. This setting must not change the shader opacity used by Cycles.

### Material Toggles

- A converted material's optional nodes follow its material properties. Every rebuild of the opacity flow (Convert on a converted material, `Apply Opacity`, and a toggle change) must recreate or remove those nodes from the properties; never drop an enabled toggle or leave a disabled toggle's nodes behind.
- Helpers that walk the flow from the Material Output, such as finding the Toon BSDF or the source alpha, must look through the optional nodes.
- A toggle must not change a material that has no `CyclesTooner_Opacity` node.
- `No Shadow` (`cyclestooner_no_shadow`) inserts the `CyclesTooner_ShadowTransparency` Math node (`MAXIMUM`) between `CyclesTooner_Transparency` and the `CyclesTooner_OpacityMix` factor, with the `Is Shadow Ray` output of the `CyclesTooner_LightPath` node as its second input. Enabling it also enables the material's Transparent Shadows setting, because Cycles otherwise ignores shader transparency for shadow rays.
- `Emission` (`cyclestooner_emission`) inserts the `CyclesTooner_EmissionMix` Mix Shader between the Toon BSDF and the first shader input of `CyclesTooner_OpacityMix`, with the Toon BSDF as its first shader and the `CyclesTooner_Emission` node as its second. Its factor is the material's `cyclestooner_emission_factor` (default `0.5`): `0` matches the toggle being off and `1` shows the unshaded color. The UI shows the factor only while the toggle is on.
- On every rebuild, connect the Emission `Color` to the same source socket as the Toon BSDF `Color`, or copy the Toon BSDF color value when it is unlinked. Leave the Emission `Strength` as it is; the add-on controls the look through the mix factor only.
- Revert removes the optional nodes and turns the toggles off.

### Source Shader Classification

- Direct MMDShaderDev, MToon, and VRToon conversion should preserve available base color, texture color/alpha, normal links, and material alpha as far as the current converter supports.
- Do not classify an ordinary Principled BSDF material as MToon solely because the VRM add-on attached disabled MToon extension data to it.
- MToon conversion must ensure a `Material Output` exists after conversion, because VRM shader groups may hide output internally.
- Classify VRToon only when a shader group whose node-tree name starts with `VRToon` is connected to the active Material Output. Do not classify an unused group elsewhere in the material as the source shader.
- VRToon `Alpha` and `Material Alpha` must be combined through the shared CyclesTooner opacity flow.
- MToon and MMD conversion must preserve the upstream nodes that provide base-texture UV transformations and linked normals.

### Unitypackage Importer

- Classify UnityToon only when a group node connected to the active Material Output `Surface` uses a node tree whose `unitypkg_version` custom property is a supported version (currently `1`), has `Base Color`, `Alpha`, and `Normal` inputs, and has a `Shader` output of type `SHADER`.
- UnityToon conversion preserves the `Base Color` connection or value, including its texture, tint, and UV chain; the `Normal` connection; and the `Alpha` connection or value through the shared opacity flow.
- After removing the UnityToon node, remove its node group only when it is a local data block with no remaining users and no fake user.
- Classify an Unlit material only when an `Emission` node labeled `Unlit` is connected to the Material Output, either directly or as the second shader of a Mix Shader whose first shader is a `Transparent BSDF`. The Mix Shader factor becomes the alpha source.
- Never convert an ordinary Emission node that lacks the `Unlit` label.
- Unlit conversion removes only the replaced Emission, Mix Shader, and Transparent BSDF nodes.

### Revert

- Revert restores a simplified `Principled BSDF` material. It does not reconstruct MMDShaderDev, MToon, VRToon, or UnityToon node setups, and user-facing documentation must say so.

### Node Cleanup and Layout

- Conversion cleanup should remove unused source shader groups and disconnected nodes created only for the old shader path.
- Conversion cleanup must preserve every path connected to any Material Output input, including Surface, Volume, and Displacement.
- Do not delete an unknown disconnected node merely because it is unreachable from Material Output. Collect unknown top-level nodes and node groups in the `CyclesTooner Preserved Nodes` frame.
- Remove dangling Reroute nodes, fully unlinked Mix Shader and Add Shader nodes, and empty Frames during converted-node cleanup. Preserve shader combiners that retain any input or output connection.
- Arrange converted material nodes by their connection depth. Keep reachable nodes outside legacy source Frames and consolidate preserved disconnected components without breaking their internal links.

## User Interface Text

- Write every operator report, tooltip (`bl_description`), and property description in English, and add its Japanese translation to `translations.py`.
- Translate a report with `report_message()` before filling in its values; never pass an f-string to `self.report`.
- Keep button and panel labels (`bl_label` and layout `text=`) in English so that they match the READMEs and GitHub Pages.
- Blender's own dictionary translates common words such as `Convert`, `Revert`, and `Opacity`. To keep labels in English in every language, give each operator `bl_translation_context = LABEL_CONTEXT` and each property `translation_context=LABEL_CONTEXT` (from `translations.py`), and pass `translate=False` with every layout `text=`. Register no translations under `LABEL_CONTEXT`; tooltips and descriptions are translated through the default context and are unaffected.

## Outline

### Add Outline

- `Add Outline` is object-driven, not active-collection-driven.
- The outline target is the selected active object's topmost parent, including Empty roots.
- `Add Outline` should create this hierarchy:

```text
Root_Collection
├─ Root
│  └─ child objects...
└─ Root_Outline_Collection
   ├─ Root_Outline
   └─ Root_Outline_Source
```

- Every object under the root hierarchy should be moved into `Root_Collection`; do not leave child objects in the original generic collection.
- `Root_Outline_Source` should link only render-visible mesh objects used by Geometry Nodes. Render-hidden meshes, non-mesh objects, and generated outline objects must not be outline sources.
- After `Add Outline`, exclude `Root_Outline_Source` from the active View Layer while keeping Geometry Nodes outline evaluation working.
- `Add Outline` should configure the Geometry Nodes `Weight` input to use the `CT_Outline` attribute.
- For every outline source mesh, `Add Outline` should create a `CT_Outline` vertex group with all vertices initialized to weight `0.5` when the group does not exist.
- If an outline source mesh already has a `CT_Outline` vertex group, preserve the group and all of its existing weights unchanged.
- The outline node group must delete every face whose offset distance (`Weight * Thickness`, averaged over the face) is `1e-6` or less, before offsetting. Such a face would coincide with the model surface, and Cycles renders coincident faces with artifacts or drops the surface on GPU devices.

### VRToon Outline Preparation

- During Convert, prepare each recognized VRToon `vrt_outline` setup without creating a CyclesTooner outline: preserve an existing `CT_Outline`, otherwise set it from `vrt_outline_thick * vrt_outline_mask`, and store the median source Solidify Thickness on the model root.
- Treat a missing VRToon weight group differently from a missing vertex assignment: use `0.5` when `vrt_outline_thick` is absent, use `1.0` when `vrt_outline_mask` is absent, and use `0.0` for an unassigned vertex in a group that exists.
- Remove a VRToon outline modifier and its `vrt_outline_mat` slots only after its `CT_Outline` preparation succeeds. Recognize the modifier using its `vrt_outline` name, `SOLIDIFY` type, `vrt_outline*` vertex group, and flipped normals; do not remove modifiers based on name alone.
- Convert must not create the CyclesTooner outline. `Add Outline` should use the prepared root Thickness when present and the prepared `CT_Outline` weights when they exist.

### Refresh Outline

- `Refresh Outline` must require an actual selected model part or generated outline. Do not refresh from `context.collection` when nothing relevant is selected.
- `Refresh Outline` should rebuild the source collection from the current root hierarchy while preserving the existing outline object, material, node group, and modifier values.
- `Refresh Outline` adds the zero-offset face deletion to a node group created by an earlier version. It must not change the group in any other way.
- If no render-visible mesh source is found during refresh, cancel and keep the existing source collection intact.

### Remove Outline

- `Remove Outline` should remove the generated outline object, its source collection, empty outline container collection, and unused outline data blocks where safe.
