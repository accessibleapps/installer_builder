# Document the existing Python requirement

## Goal

Correct README's Python 2.5 statement to the actual pyproject minimum, 3.8.6.
Smallest change: one documentation line; no support policy or runtime change.

## State

Worker thread `01a15b4c-eda9-7420-bdff-05199b061038`. Exact origin
`https://github.com/accessibleapps/installer_builder`; fresh master base
`099ceb30876aba2b853a8bb98815cba3bb19f3e9`. New branch
`modernize/task6-installer_builder`, isolated worktree directly under task-6.
Canonical tracked state clean; 1,671 untracked environment/history/source files
and lock preserved. Existing PR #1 only changes Dependabot configuration.

## Decisions and why

Read global instructions, untracked canonical CLAUDE, README, pyproject, core,
capability/translation tests and both tracked integration files. README says
Python 2.5, while pyproject requires >=3.8.6. Characterization is this direct
documentation/metadata mismatch; do not add a test or alter package requirements
for a one-line documentation correction. Existing test authority is README's
`uv run pytest` (also recorded in topology). The sole GitHub workflow is dynamic
Dependabot Dependency Graph, not a test/build gate. Run documented full suite
once under the coverage assignment's no-hosted-test settlement. The tests mock
compiler/freezer/signing surfaces; no live installer/signing action is authorized.

## Surprises

Canonical CLAUDE mentions obsolete setup.py/main.py commands, but is untracked
user material. Preserve it. No tracked uv.lock exists; any resolver output stays
isolated and is not part of this documentation slice.

## Next step

Correction applied. `uv run pytest` passed: 62 tests, 3 existing warnings,
4.60 s, CPython 3.13.15 / pytest 9.1.1. No live freezer/compiler/signing action
ran. pyproject diff remains empty. Resolver created an untracked isolated uv.lock
and Python caches; none are included. Canonical untracked material is untouched.
No configured hooksPath or active hook files exist. Commit only README and this
note, then return the patch for coordinator review before push/publication.
