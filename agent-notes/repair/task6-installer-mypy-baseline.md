# Goal

Measure the full configured installer_builder mypy baseline before changing
the dependency range in original same-org PR #4. Preserve package >=3.8.6,
mypy target 3.8 and every existing strict setting.

# State

repair/task6-installer-mypy-baseline is locally rebased onto verified merged
master 11ec654ac80ef0bd7423156e76a22aa1d8e3a453 using --no-update-refs. Draft
prerequisite #5 remains open and unmerged at published old head
748ddadfa400a596a12a03e32fc1923c99705dd5; this rebased successor is unpublished.
The workflow adds only three lines in the existing Windows Python 3.8 leg.
Current optional dev extra remains mypy>=0.991,<1.0. No full package checker
command has run locally.

# Decisions and why

- The new explicit baseline scope is `python -m mypy --config-file pyproject.toml
  --package installer_builder`, invoked through `uv run --extra dev`. This is
  newly wired coverage of all four production modules, not a previously
  authoritative command or a tiny probe claimed to cover the whole package.
- Existing CI installs pytest through the dependency group, but does not select
  the separate optional mypy extra. The added step selects that extra on the
  existing 3.8 runtime, honoring the unchanged 3.8 target.
- Diagnostics fail normally. No continue-on-error, ignored diagnostic codes,
  altered strict flags, target substitution, skip or mass annotation is added.
  Existing source contains unannotated definitions; hosted CI must establish
  actual diagnostics before deciding any bounded baseline repair.
  The first hosted baseline has now established those diagnostics below.
- The existing Windows 3.8/3.14 test/build axes, check names, action pins,
  permissions, checkout credentials policy, timeout and concurrency remain.
  A failing baseline step prevents that leg's later build in the usual way;
  it is not a green baseline and does not justify suppressing the failure.
- Any later compatibility probe and dependency narrowing stay separate. A probe
  of config/target/API behavior is not full-package typecheck evidence.

# Preservation

backup/task6-installer-mypy-original-pr preserves original PR #4 head
62d473dd04ad154d3b4aade2b8723dc76ce73909. Canonical local master remains
099ceb30876aba2b853a8bb98815cba3bb19f3e9 with all untracked user environments,
history, lock and source files preserved. Other branches/worktrees/backups
are untouched. Named archive/task6-installer-mypy-baseline-before-11ec preserves
748ddadfa400a596a12a03e32fc1923c99705dd5 and
archive/task6-installer-mypy-compatibility-before-11ec preserves
e89bff687780f0aa2a426f2047cb4467a917f584. No remote PR branch or default branch
was changed by this local rebase.

# Verification

Historically, actionlint 1.7.12 passed with optional shellcheck/pyflakes disabled
and zizmor 1.31.1 offline pedantic reported no findings for the unchanged added
workflow step. Hosted run 39548810883 at old head 748ddadf failed the full
configured package check with 115 errors in four files using the existing <1.0
tool; its Python 3.14 tests/build passed. That result is historical evidence,
not a result for this rebased head. The merged #6 base contains separate legacy
helper fixes and 71-test coverage; remaining baseline diagnostics need fresh
hosted measurement. No local full checker, tests/build or installer/signing
action ran, including during this rebase. Complete delta inspection confirms
the same three-line gate, unchanged strict flags, target and dependency range.

# Next step

Return the clean rebased local commit/full diff for coordinator review before
guarded publication of draft #5 and fresh hosted baseline measurement. Keep
the one-line original dependency proposal unchanged. Draft #5 has not landed.
No Claude, blocked review route, QActivate, settings, remote write, merge or
release.
