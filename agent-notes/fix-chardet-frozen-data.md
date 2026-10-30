# Collect chardet's frozen runtime inputs

## Goal

Repair shared Windows freezing for current compiled chardet, as exposed by QSeek PR #1. Q authorized QSeek modernization including current shared packages and directed checking how sibling apps solve packaging before adding a local workaround.

## State

Independent branch fix/chardet-frozen-data starts from refreshed integrated installer_builder master in this isolated worktree. The canonical sibling checkout has unrelated local work and is untouched. QSeek's downloaded CI artifact fails startup when html_to_text imports chardet: its compiled pipeline wrapper cannot import chardet.pipeline.orchestrator__mypyc. The shared hook is implemented and registered beside the existing Jinja2 hook. Three focused tests pass using QSeek's current Python environment with this owner source first on the import path. No full local suite, typecheck, build, commit or publication was run.

## Decisions and why

The current shared builder already registers package-specific py2exe hooks (Jinja2). Sibling products provide package inputs to that owner, rather than copy hooks into each application. Use that same owner: roughly 20 source lines for chardet's existing compiled subpackages and model resource files, plus focused meaningful tests. Native finder package collection is only first-level, so root-only collection is insufficient. Five model .bin files are read with importlib.resources and belong inside the chardet/models archive path. Older chardet layouts without these subpackages must continue to package normally. Do not introduce a new packaging abstraction, disable compiled extensions, pin around the defect, or change signing/locale/build checks.

The hook queues chardet root and its actually present pipeline/models subpackages through import_package_later, which lets py2exe discover neighboring native helper modules using its existing extension-suffix handling. Actual models/*.bin files are added to the ZIP with forward-slash package paths; unrelated training YAML is excluded. Tests exercise the real finder's immediate-member enumeration and read the collected model bytes through importlib.resources from a ZIP-backed package. These are focused collection-contract tests, not proof of successful native loading or packaged startup.

## Surprises

The product's py2exe build and source tests pass while the built application fails startup. Actual downloaded-artifact behavior is the evidence. QSeek's intentional source debug listener remains enabled; this task does not change application behavior or activation. Test authority is the tracked README's uv run pytest, with no tracked owner lock. Owner build/release command authority is unavailable; no release is part of this repair.

## Next step

Root reviews the three owned file changes, publishes an independent owner PR and reads its full CI. QSeek must consume the integrated owner change after it is merged, without stacking PRs or pointing at an unmerged branch. Root owns all publication and merge decisions; workers do not publish. A rebuilt QSeek artifact must still verify the native loading and model-resource behavior end to end.
