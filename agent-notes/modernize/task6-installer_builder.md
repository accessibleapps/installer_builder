# Document the Python requirement and host the safe suite

## Goal

Correct README's Python 2.5 statement to the actual pyproject minimum, 3.8.6.
The original slice was one documentation line; its safe test/build documentation
and living note remain. The reviewed suite/build workflow is now in merged
baseline PR #3. No source, dependency, signing or support-policy change.

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

## Historical CI follow-up

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

## Historical CI audits

Final authored YAML passed actionlint 1.7.12 and zizmor 1.31.1 --offline --pedantic
with zero findings; optional actionlint shellcheck/pyflakes integrations disabled.
Complete workflow/README/note diff inspected; source/tests/manifest unchanged and
no resolver or untracked lock copied. Return the exact committed local head for
coordinator review before any publication. Historical 62-pass result above is
not new final-head hosted evidence. Do not rerun local full CI, suppress default
failures, call external reviewers, publish, merge or change settings under this
initial local-patch authority.

## Historical local stack preparation

Published draft PR #2 advanced to b57d20b46bab111b41f40115ccbcca22a4b8274a. Its
CI exposed the existing master Python 3.8 test syntax defect. Green prerequisite
e45937f8a16565e0160621b956d3b5fb3bb9aefe fixed that syntax and hosted the same
tests/build (62 passed per Windows 3.8/3.14, run 39524730407). Before it merged,
local stack 78bafc57c7835a52fe45297064212e0bae988ebc merged full b57 onto e459,
retaining all feature work. That exact stack is archived before this rebase.

## Historical landed-base rebase

Baseline PR #3 is now merged as 8f5d7f28381066ec3bafac95468e3d7970261d58 after
actual review and green hosted tests/build. Fresh remote master is that exact
commit; its tree equals e45937f, but the real squash is the required new ancestor.
The original PR remains OPEN/DRAFT at b57d20b; canonical local master stays
099ceb3 and original local feature stays 8c90263 with all user work untouched.

Only isolated repair/task6-installer-feature-successor was genuinely rebased via
--no-update-refs --onto 8f5d7f2 e45937f. It replays the two original feature
commits onto landed master. Ordinary rebase omits edits made inside the old local
merge, so this living note retains that stack history and updates the current
handoff. Full approved README is byte-identical to old stack 78bafc5; workflow,
source, tests and manifest are identical to landed master.

Separate before-landed-rebase refs preserve old stack 78bafc5, original local
feature 8c90263 and current published b57d20b, plus all earlier archives. Explicit
--no-update-refs was used because global rebase.updateRefs is true. No remote
branch movement, local full CI, model invocation or unrelated changes occurred.

## Current rebase after Dependabot merged

PR #1 merged as ad7a2a1326484ba8ca12eb7a690de4d2607d6dbe after its actual
Claude review and green hosted matrix. Fresh authenticated origin/master is that
exact commit. PR #2 remains published at a22928e6b91db9e5f071034156dc76d73fe4da58;
backup/task6-installer-feature-{local,published}-before-dependabot-rebase preserve
that exact tip, and the detached review checkout plus every older archive remain.

Genuinely rebased repair/task6-installer-feature-successor with --no-update-refs
--onto ad7a2a1 8f5d7f2. All three feature commits replayed cleanly, preserving
the complete README correction/documentation and the newly landed Dependabot
configuration and schema CI step. Source, tests, workflow and manifest equal
current master. Canonical dirty work and original feature worktrees are untouched.

Hosted run 39535871457 and Claude's two-pass no-findings review/gate cover old
a22928e only; they are historical evidence, not approval of this new local head.
No new hosted result or review exists yet. No push, full local CI, model call,
native tool invocation, settings change or description edit occurred.

## Next step

Return the complete local head/diff for coordinator review before any publication.
Recapture live default and original local/published tips, then obtain exact-head
guarded publication authority. Full final-head hosted checks and actual review
remain required before merge; baseline results are not successor results.
No description, settings/security, release or remote merge action is authorized.
