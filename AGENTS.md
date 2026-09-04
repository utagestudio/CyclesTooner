# Agent Notes

## Project Rules

- This is a Blender add-on for Cycles toon rendering. Keep changes scoped to the add-on files unless the user explicitly asks for repository or release automation work.
- Do not commit `_temp/`, `__pycache__/`, screenshots, or other local verification artifacts.
- Prefer small, behavior-focused commits. Commit messages should use a concise title, a blank second line, then details from the third line onward.
- Unless the user explicitly asks to leave work uncommitted, commit completed work before reporting completion.
- Skip the automatic commit only when there is a concrete reason, such as incomplete or failing work, unresolved user-owned changes that cannot be separated safely, or a required user decision. State the reason when work is left uncommitted.
- Preserve existing author, maintainer, and contributor attribution unless the task explicitly includes an attribution change.
- Do not add an AI system, coding agent, or tool as an author or contributor merely because it was used during development.
- If `AGENTS.local.md` exists, follow it for machine-specific tooling and connection details. Never commit that file.

## Versioning

- Follow `VERSIONING.md` as the canonical versioning and release policy.
- Versions follow `MAJOR.MINOR.PATCH[-dev.N]`:
  - Increment `MAJOR` only for an explicitly planned breaking release.
  - Increment `MINOR` for backward-compatible feature releases.
  - Increment `PATCH` for backward-compatible bug-fix releases.
  - Use `-dev.N` for committed development work targeting the next release.
- Choose the target release before development begins. For example, feature work after `1.21.0` starts at `1.22.0-dev.1`, not `1.21.1`.
- Increment `N` once for every commit containing program changes to the Blender add-on. Committing non-zero development versions is expected.
- When merging the completed release into `main`, remove `-dev.N` without changing the already selected `MAJOR.MINOR.PATCH`; for example, `1.22.0-dev.5` becomes `1.22.0`.
- Do not change the add-on version for documentation, GitHub Pages, repository metadata, or other non-program changes unless the user explicitly requests it.
- Before every `git commit` or `git commit --amend`, do a dedicated version check:
  - If the commit contains program changes, increment the `dev.N` counter exactly once.
  - If the commit contains only non-program changes, keep the existing version unchanged.
  - For a release commit merged into `main`, remove the prerelease suffix and keep the target release core unchanged.
  - Keep the core version in `__init__.py` and the full version in `blender_manifest.toml` synchronized in the same commit.
- `bl_info["version"]` contains only the integer `(MAJOR, MINOR, PATCH)` tuple. `ADDON_VERSION_PRERELEASE` and `ADDON_VERSION_STRING` in `__init__.py` carry the development suffix used by the manifest.

## Release History

- When preparing a completed development branch for merge into `main`, update the GitHub Pages release history in both `.github/pages/index.html` and `.github/pages/ja/index.html` as part of the release work. Do not limit the release task to changing version numbers.
- Add one entry for the final release version, with the release date, a concise title, and a detailed list summarizing the user-visible fixes and features developed on that branch.
- Derive the entry from the branch's actual commits and resulting behavior. Consolidate related implementation commits into clear release notes instead of copying commit subjects verbatim.
- Keep the English and Japanese entries equivalent, place the newest release first, and leave only the newest entry expanded by default.
- Keep no more than six release entries on each landing page. When adding a seventh entry, remove the oldest entry from both the English and Japanese pages so that the two histories remain aligned.
- Documentation-only or GitHub Pages-only branches do not require a release-history entry unless they are themselves part of an add-on release.

## Commit Checklist

Before committing or amending, complete these steps in order:

1. Determine whether the commit contains add-on program changes, only non-program changes, or is the release commit for `main`.
2. Set the target and development version according to the Versioning rules above.
3. For a release being merged into `main`, add the corresponding bilingual GitHub Pages release-history entry described above.
4. Run:
   - `python3 -m py_compile __init__.py operators_converter.py operators_outline.py ui.py`
   - `git diff --check`
5. Remove generated `__pycache__/`.
6. Stage only the intended files, excluding `_temp/`, `__pycache__/`, screenshots, and unrelated local artifacts.
7. Run `git diff --cached --check`.
8. Re-check the staged core version, prerelease suffix, full version string, manifest version, and release-history entry before `git commit` or `git commit --amend`.

## Verification

- Before reporting completion or committing, run:
  - `python3 -m py_compile __init__.py operators_converter.py operators_outline.py ui.py`
  - `git diff --check`
- Remove generated `__pycache__/` after running `py_compile`.
- If Blender runtime behavior is changed, mention that local Python checks passed but Blender UI verification still needs Blender-side testing unless it was actually tested in Blender.
- When Blender MCP is available, use it for runtime verification where Blender-side behavior needs to be checked, especially for UI, operators, material conversion, outline hierarchy, and scene state.
- When Blender MCP is connected during development and program files change, update the CyclesTooner add-on installed in the connected Blender through MCP before Blender-side verification. Create a timestamped backup inside the installed add-on directory before overwriting files, reload/re-enable the add-on, then verify against the updated installed copy.
- If Blender MCP tools are unavailable or the connection appears inactive, report that Blender-side verification could not be completed and refer to `AGENTS.local.md` when it exists.

## Material Conversion Rules

- Toon BSDF `Smooth` default is `0.2`.
- Principled BSDF conversion should preserve a linked `Base Color` source. When `Base Color` is unlinked, copy its configured socket color to the Toon BSDF.
- Opacity control is unified through the CyclesTooner opacity flow; do not create a separate MMD/MToon/VRToon alpha flow.
- Direct MMDShaderDev, MToon, and VRToon conversion should preserve available base color, texture color/alpha, normal links, and material alpha as far as the current converter supports.
- Do not classify an ordinary Principled BSDF material as MToon solely because the VRM add-on attached disabled MToon extension data to it.
- MToon conversion must ensure a `Material Output` exists after conversion, because VRM shader groups may hide output internally.
- Classify VRToon only when a shader group whose node-tree name starts with `VRToon` is connected to the active Material Output. Do not classify an unused group elsewhere in the material as the source shader.
- VRToon `Alpha` and `Material Alpha` must be combined through the shared CyclesTooner opacity flow.
- Conversion cleanup should remove unused source shader groups and disconnected nodes created only for the old shader path.
- MToon and MMD conversion must preserve the upstream nodes that provide base-texture UV transformations and linked normals.
- Conversion cleanup must preserve every path connected to any Material Output input, including Surface, Volume, and Displacement.
- Do not delete an unknown disconnected node merely because it is unreachable from Material Output. Collect unknown top-level nodes and node groups in the `CyclesTooner Preserved Nodes` frame.
- Remove dangling Reroute nodes, fully unlinked Mix Shader and Add Shader nodes, and empty Frames during converted-node cleanup. Preserve shader combiners that retain any input or output connection.
- Arrange converted material nodes by their connection depth. Keep reachable nodes outside legacy source Frames and consolidate preserved disconnected components without breaking their internal links.

## Outline Rules

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
- During Convert, prepare each recognized VRToon `vrt_outline` setup without creating a CyclesTooner outline: preserve an existing `CT_Outline`, otherwise set it from `vrt_outline_thick * vrt_outline_mask`, and store the median source Solidify Thickness on the model root.
- Treat a missing VRToon weight group differently from a missing vertex assignment: use `0.5` when `vrt_outline_thick` is absent, use `1.0` when `vrt_outline_mask` is absent, and use `0.0` for an unassigned vertex in a group that exists.
- Remove a VRToon outline modifier and its `vrt_outline_mat` slots only after its `CT_Outline` preparation succeeds. Recognize the modifier using its `vrt_outline` name, `SOLIDIFY` type, `vrt_outline*` vertex group, and flipped normals; do not remove modifiers based on name alone.
- Convert must not create the CyclesTooner outline. `Add Outline` should use the prepared root Thickness when present and the prepared `CT_Outline` weights when they exist.
- `Refresh Outline` must require an actual selected model part or generated outline. Do not refresh from `context.collection` when nothing relevant is selected.
- `Refresh Outline` should rebuild the source collection from the current root hierarchy while preserving the existing outline object, material, node group, and modifier values.
- If no render-visible mesh source is found during refresh, cancel and keep the existing source collection intact.
- `Remove Outline` should remove the generated outline object, its source collection, empty outline container collection, and unused outline data blocks where safe.
