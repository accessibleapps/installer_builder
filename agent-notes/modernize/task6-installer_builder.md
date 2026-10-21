# Document the Python requirement and host the safe suite

## Goal

Correct README's Python 2.5 statement to the actual pyproject minimum, 3.8.6.
The original slice was one documentation line. Current authorized follow-up adds
minimal existing full-suite/package CI, about 40 YAML lines plus README and this
existing living note. No source, dependency, signing or support-policy change.

## Historical first-pass state

Worker thread `01a15b4c-eda9-7420-bdff-05199b061038`. Exact origin
`https://github.com/accessibleapps/installer_builder`; fresh master base
`099ceb30876aba2b853a8bb98815cba3bb19f3e9`. New branch
`modernize/task6-installer_builder`, isolated worktree directly under task-6.
Canonical tracked state clean; 1,671 untracked environment/history/source files
and lock preserved. Existing PR #1 only changes Dependabot configuration.

## Historical first-pass decisions

Read global instructions, untracked canonical CLAUDE, README, pyproject, core,
capability/translation tests and both tracked integration files. README says
Python 2.5, while pyproject requires >=3.8.6. Characterization is this direct
documentation/metadata mismatch; do not add a test or alter package requirements
for a one-line documentation correction. Existing test authority is README's
`uv run pytest` (also recorded in topology). The sole GitHub workflow is dynamic
Dependabot Dependency Graph, not a test/build gate. Run documented full suite
once under the coverage assignment's no-hosted-test settlement. The tests mock
compiler/freezer/signing surfaces; no live installer/signing action is authorized.

## Historical first-pass surprises

Canonical CLAUDE mentions obsolete setup.py/main.py commands, but is untracked
user material. Preserve it. No tracked uv.lock exists; any resolver output stays
isolated and is not part of this documentation slice.

## Historical first-pass validation

Correction applied. `uv run pytest` passed: 62 tests, 3 existing warnings,
4.60 s, CPython 3.13.15 / pytest 9.1.1. No live freezer/compiler/signing action
ran. pyproject diff remains empty. Resolver created an untracked isolated uv.lock
and Python caches; none are included. Canonical untracked material is untouched.
No configured hooksPath or active hook files existed. That reviewed documentation
slice was published as draft PR #2 at 8c9026344324e4cc875b94b4b7a62e650c35f5c2.

## Current CI follow-up

- Fresh default remains master 099ceb30876aba2b853a8bb98815cba3bb19f3e9. Existing
  OPEN/DRAFT PR #2, original local feature branch and published remote tip all
  match 8c9026344324e4cc875b94b4b7a62e650c35f5c2. Named refs
  backup/task6-installer-builder-local-before-ci and
  backup/task6-installer-builder-published-before-ci preserve both original tips.
- New isolated worktrees/installer-builder-ci on repair/task6-installer-builder-ci
  starts at that exact feature tip. Canonical untracked user/environment files and
  original feature's untracked lock/caches are preserved, with no reset/stash/clean.
- Re-read global and canonical untracked CLAUDE guidance, tracked source/README/
  manifest and all four test modules before changes. Canonical CLAUDE's setup.py
  build instruction is obsolete; pyproject uses hatchling, and current explicit
  task authorizes the narrow nonpublishing uv build package gate.
- The real full suite imports winreg-backed signing and patches py2exe.freeze;
  Windows is required to exercise these existing contracts without added skips
  or new platform mocks. Tests replace signer/compiler/freezer calls and use
  synthetic metadata and temporary files; actual native tools are not invoked.
- Coordinator settled Windows Python 3.8 and 3.14. Manifest floor is >=3.8.6;
  upstream py2exe 0.13.0.2 supports >=3.8,<3.12 and has cp38 Windows wheels;
  current 0.14.2.0 supports >=3.10,<3.15 with cp314 Windows wheels. Python 3.15
  is stable upstream but is outside that dependency's installable ceiling.
  Record this limit, do not change support metadata or claim 3.15 coverage.
- Public innosetup_builder Git dependency still declares >=3.8.6 and is accessible
  without credentials. Existing manifest/dependency policy remains unchanged;
  no tracked lock exists, and no canonical/feature untracked lock is copied.
- Actions enabled confirmed read-only. Dependabot #1 at
  50f710fe75c412dea43186007c5b50af2516ce10 only adds .github/dependabot.yml;
  this task does not edit that file, its branch, PR description or any settings.
- CI uses ordinary PR/master pushes, read-only permissions, pinned verified
  checkout/setup-uv actions, no persisted checkout credentials/cache/secrets,
  timeout/concurrency, the exact README uv run pytest command, then uv build and
  nonempty wheel/sdist checks. No runtime test source, package metadata or native
  installer/signing/release workflow changes.

## Next step

Final authored YAML passed actionlint 1.7.12 and zizmor 1.31.1 --offline --pedantic
with zero findings; optional actionlint shellcheck/pyflakes integrations disabled.
Complete workflow/README/note diff inspected; source/tests/manifest unchanged and
no resolver or untracked lock copied. Return the exact committed local head for
coordinator review before any publication. Historical 62-pass result above is
not new final-head hosted evidence. Do not rerun local full CI, suppress default
failures, call external reviewers, publish, merge or change settings under this
initial local-patch authority.
