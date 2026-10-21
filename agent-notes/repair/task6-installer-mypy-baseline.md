# Goal

Measure the full configured installer_builder mypy baseline before changing
the dependency range in original same-org PR #4. Preserve package >=3.8.6,
mypy target 3.8 and every existing strict setting.

# State

Local-only repair/task6-installer-mypy-baseline starts at verified merged master
e59336b7b5acb88d76d829dc9b61ac6585ba189d. The workflow adds only three lines in
the existing Windows Python 3.8 leg. Current optional dev extra remains
mypy>=0.991,<1.0. No full package checker command has run locally.

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
history, lock and source files preserved. Existing branches/worktrees/backups
are untouched. No same-org PR branch or default branch was changed.

# Verification

No local full checker, tests/build or installer/signing action ran. Actionlint
1.7.12 passed with optional shellcheck/pyflakes disabled. Zizmor 1.31.1 offline
pedantic reported no findings. Complete diff inspection is the other local
check; no action pins or permissions changed. Actual
hosted baseline diagnostics remain pending coordinator publication of this
reviewable local candidate. No checker results/counts are inferred from source.

# Next step

Return the clean local commit/full diff for coordinator review and separate
draft publication authority so hosted CI measures the current configured
baseline. Keep the one-line original dependency proposal unchanged. No Claude,
blocked review route, QActivate, settings, remote write, merge or release.
