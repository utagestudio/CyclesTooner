# Versioning, Commit, and Release Policy

CyclesTooner uses Semantic Versioning with a development prerelease suffix:

```text
MAJOR.MINOR.PATCH[-dev.N]
```

## Version meanings

- `MAJOR` changes only for releases that intentionally break existing usage or compatibility.
- `MINOR` changes for backward-compatible features and improvements.
- `PATCH` changes for backward-compatible bug fixes.
- `dev.N` identifies committed development work toward an already selected release. `N` starts at `1` and increases once for every commit containing add-on program changes.

Select the destination version before implementation begins. Development after `1.21.0` for a feature release therefore proceeds as follows:

```text
1.21.0
1.22.0-dev.1
1.22.0-dev.2
1.22.0-dev.3
1.22.0
```

Development for a bug-fix release uses the same pattern:

```text
1.21.0
1.21.1-dev.1
1.21.1-dev.2
1.21.1
```

The final release never rewinds or increments the selected core version. It only removes the prerelease suffix: `1.22.0-dev.5` becomes `1.22.0` when the completed release is merged into `main`.

## Version sources

`__init__.py` defines three related values:

```python
ADDON_VERSION = (1, 22, 0)
ADDON_VERSION_PRERELEASE = "dev.5"
ADDON_VERSION_STRING = ".".join(map(str, ADDON_VERSION))
if ADDON_VERSION_PRERELEASE:
    ADDON_VERSION_STRING = f"{ADDON_VERSION_STRING}-{ADDON_VERSION_PRERELEASE}"
```

`bl_info["version"]` uses `ADDON_VERSION` because Blender requires an integer tuple there. `blender_manifest.toml` uses the complete Semantic Versioning string and must match `ADDON_VERSION_STRING`.

For a final release, set `ADDON_VERSION_PRERELEASE` to an empty string and use the core version in the manifest:

```python
ADDON_VERSION = (1, 22, 0)
ADDON_VERSION_PRERELEASE = ""
ADDON_VERSION_STRING = ".".join(map(str, ADDON_VERSION))
```

```toml
version = "1.22.0"
```

## Branches and pull requests

- Start every implementation task on a new topic branch from the latest `main`; do not commit task work directly on `main`.
- Name branches by purpose: `feature/<topic>` for features, `fix/<topic>` for bug fixes, and `docs/<topic>` for documentation-only work.
- Merge completed branches into `main` through a GitHub pull request. Pushing to `main` publishes the extension repository and GitHub Pages.

## Commit rules

- Prefer small commits centered on one behavior or purpose.
- Commit completed work before reporting completion unless the user explicitly asks to leave it uncommitted.
- Leave work uncommitted only for a concrete reason, such as incomplete or failing work, changes that cannot be separated safely from unrelated user work, or a required user decision. Report that reason clearly.
- Before committing program changes, increment `dev.N` exactly once and update both version sources in the same commit.
- A commit containing multiple files for one coherent program change still increments `dev.N` only once.
- Documentation, GitHub Pages, repository metadata, and other non-program-only commits do not change the add-on version.
- The release commit for `main` removes `-dev.N`; it does not increment the already selected core version.
- Do not publish or treat a `-dev.N` build as a final release.
- Commit messages use a concise title, a blank second line, and details from the third line onward.

Parallel development branches may select the same `dev.N`. Resolve this before integration by rebasing or assigning the next available development number so the integrated history has an unambiguous sequence.

## Release history

The GitHub Pages landing pages carry the user-facing release history. When preparing a completed development branch for merge into `main`, update it as part of the release commit; do not limit the release to changing version numbers.

- Add one entry for the final release version to both `.github/pages/index.html` and `.github/pages/ja/index.html`, with the release date, a concise title, and a list of the user-visible fixes and features developed on that branch.
- Derive the entry from the branch's actual commits and resulting behavior. Consolidate related implementation commits instead of copying commit subjects.
- Write each item from the user's point of view: what now works differently in Blender. Leave out internal mechanisms such as function names, data paths, and evaluation order.
- Keep the English and Japanese entries equivalent, place the newest release first, and leave only the newest entry expanded by default.
- Keep no more than six entries on each page. When adding a seventh, remove the oldest entry from both pages.
- Documentation-only or GitHub Pages-only branches do not require an entry unless they are part of an add-on release.

## Commit checklist

Before committing or amending:

1. Classify the commit as a program change, a non-program change, or the final release commit.
2. Update or preserve the version as required above, keeping `__init__.py` and `blender_manifest.toml` synchronized.
3. For a final release commit, add the bilingual release-history entry.
4. Run:

   ```bash
   python3 -m py_compile *.py
   git diff --check
   ```

5. Remove the generated `__pycache__/`.
6. Stage only intended files; exclude `_temp/`, `__pycache__/`, screenshots, and local verification artifacts.
7. Run `git diff --cached --check`.
8. Re-check the staged core version, prerelease suffix, manifest version, and release-history entry before committing.
