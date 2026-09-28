# Agent Notes

CyclesTooner is a Blender add-on that makes avatar models set up with EEVEE-oriented toon shaders (VRM MToon, MMD, VRToon, Unitypackage Importer UnityToon) usable in Cycles. It replaces those shaders with Blender's built-in Toon BSDF and generates inverted-hull outlines with Geometry Nodes.

## Where Things Live

- `docs/behavior.md`: canonical add-on behavior specification. Read it before changing material conversion or outline code, and update it on the same branch when behavior changes.
- `VERSIONING.md`: canonical versioning, branch, commit, release-history, and commit-checklist policy.
- `README.md` (Japanese) and `README_en.md` (English): user documentation.
- `.github/pages/index.html` (English) and `.github/pages/ja/index.html` (Japanese): the public landing pages, including release history.
- `AGENTS.local.md`: machine-specific tooling and connection details. Follow it when it exists; never commit it.
- `_temp/`: untracked scratch space for drafts, verification scripts, and screenshots.

## Project Rules

- Keep changes scoped to the add-on files unless the user explicitly asks for repository or release automation work.
- Follow `VERSIONING.md` for branches, versions, commits, and releases. In particular, start every implementation task on a new topic branch and keep `main` aligned with its upstream until the work is intentionally merged.
- Do not commit `_temp/`, `__pycache__/`, screenshots, or other local verification artifacts.
- Unless the user explicitly asks to leave work uncommitted, commit completed work before reporting completion. When work is left uncommitted, state the concrete reason.
- Preserve existing author, maintainer, and contributor attribution in project files unless the task explicitly includes an attribution change. Do not list AI systems as authors or maintainers in project files.

## AI Attribution in Commits

- When an AI coding agent changes add-on program files, add a `Co-authored-by` trailer for each agent that made those changes, for example `Co-authored-by: Codex <noreply@openai.com>` or `Co-Authored-By: Claude <noreply@anthropic.com>` with the model name the tool provides.
- Do not add AI trailers to commits that contain only non-program changes, such as documentation, GitHub Pages, or repository metadata.
- Keep the existing Git author and committer attribution unchanged.

## Documentation Rules

- Keep `README.md` and `README_en.md` equivalent in structure and content. Apply every change to both.
- Keep the English and Japanese GitHub Pages equivalent. Apply every change to both.
- Write user documentation for Blender users: explain what happens in Blender and what users must watch for. Keep implementation details in `docs/behavior.md`.
- When a change adds or alters user-visible behavior, update the READMEs and Pages feature descriptions on the same branch.

## Verification

- Before reporting completion or committing, run the commit checklist in `VERSIONING.md`, including `python3 -m py_compile *.py` and `git diff --check`, then remove the generated `__pycache__/`.
- For Blender runtime changes, verify the relevant behavior in Blender with the add-on loaded from the current working tree. Follow `AGENTS.local.md` for machine-specific commands when it exists.
- Check against both the minimum supported Blender version in `blender_manifest.toml` and the recommended Blender version.
- Verify operators, material conversion, outline hierarchy, and scene state as relevant, using the rules in `docs/behavior.md` as acceptance criteria.
- Keep Blender verification artifacts temporary and out of commits.
- Report any visual UI behavior that still needs an interactive Blender check. If Blender-side verification cannot run, report the reason and the remaining unverified behavior.
