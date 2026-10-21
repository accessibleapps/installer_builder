# Goal

Measure the full configured installer_builder mypy baseline after the bounded
range/target compatibility change landed separately in #7. Preserve package
>=3.8.6, mypy target 3.8 and every existing strict setting.

# State

repair/task6-installer-mypy-baseline is locally rebased onto verified merged
master fad12d9a3eafa59fcd6033e54534c4eee3ed2fb7 using --no-update-refs. Draft
#5 remains open and unmerged at published old head
2f18a7922a3bec7ca31f9fadf633081403aad973; this rebased successor is unpublished.
The delta adds only the same three-line full-package gate in the existing
Windows Python 3.8 leg. The merged base now supplies mypy>=0.991,<1.15 and
the unchanged three-case target/API/config probes on tool Python 3.8 and 3.13.
The new full-package result with selected 1.14.1 remains pending hosted CI.
No full package checker command has run locally.

# Decisions and why

- The new explicit baseline scope is `python -m mypy --config-file pyproject.toml
  --package installer_builder`, invoked through `uv run --extra dev`. This is
  newly wired coverage of all four production modules, not a previously
  authoritative command or a tiny probe claimed to cover the whole package.
- Originally CI installed pytest through the dependency group without selecting
  the optional mypy extra. The landed #7 now selects that extra for its bounded
  compatibility probes. This separate full-package step uses the same extra on
  the existing 3.8 runtime, honoring the unchanged 3.8 target.
- Diagnostics fail normally. No continue-on-error, ignored diagnostic codes,
  altered strict flags, target substitution, skip or mass annotation is added.
  Existing source contains unannotated definitions; hosted CI must establish
  actual diagnostics before deciding any bounded baseline repair.
  The first hosted baseline has now established those diagnostics below.
- The existing Windows 3.8/3.14 test/build axes, check names, action pins,
  permissions, checkout credentials policy, timeout and concurrency remain.
  A failing baseline step prevents that leg's later build in the usual way;
  it is not a green baseline and does not justify suppressing the failure.
- The landed compatibility probes and dependency narrowing are separate source
  intent, now inherited once each from actual master. Those green bounded
  config/target/API probes are not full-package typecheck evidence. The rebase
  resolved one adjacent-step workflow conflict by keeping both unchanged probes
  followed by exactly one existing full-package command; no other hunk changed.

# Preservation

backup/task6-installer-mypy-original-pr preserves original PR #4 head
62d473dd04ad154d3b4aade2b8723dc76ce73909. Canonical local master remains
099ceb30876aba2b853a8bb98815cba3bb19f3e9 with all untracked user environments,
history, lock and source files preserved. Other branches/worktrees/backups
are untouched. Named archive/task6-installer-mypy-baseline-before-11ec preserves
748ddadfa400a596a12a03e32fc1923c99705dd5 and
archive/task6-installer-mypy-compatibility-before-11ec preserves
e89bff687780f0aa2a426f2047cb4467a917f584. No remote PR branch or default branch
was changed by this local rebase. Named
archive/task6-installer-mypy-baseline-before-fad12 preserves published
2f18a7922a3bec7ca31f9fadf633081403aad973. The redundant stacked probe branch
stays unchanged at fd0103dc83f89e66c12b413e87d6fa724cbfbd91; it was not rebased
or forced through duplicate conflicts. Original PR #4 remains unchanged.

# Verification

Historically, actionlint 1.7.12 passed with optional shellcheck/pyflakes disabled
and zizmor 1.31.1 offline pedantic reported no findings for the unchanged added
workflow step. Hosted run 39548810883 at old head 748ddadf failed the full
configured package check with 115 errors in four files using the existing <1.0
tool; its Python 3.14 tests/build passed. The next published baseline 2f18a792
had 112 diagnostics with mypy 0.991 in run 39552363115 after the three helper
diagnostics disappeared; both 71-test suites passed. These are historical
results under the old <1.0 range, not counts for this rebased head. Actual #7
landed the narrower compatible <1.15 range and bounded probes separately.
The full-package result with 1.14.1 needs fresh hosted measurement; no green
baseline or new diagnostic count is inferred. No local full checker,
tests/build or installer/signing action ran, including during this rebase.
Complete delta inspection confirms the same three-line unsuppressed gate and
no delta to merged source, tests, manifest, probe assertions or strict flags.
After resolving the adjacent-step conflict, actionlint 1.7.12 again exited 0
and offline pedantic zizmor 1.31.1 reported no findings. No local test or
checker execution was added to that static workflow verification.

# Next step

Return the clean rebased local commit/full diff for coordinator review before
guarded publication of draft #5 and fresh hosted baseline measurement under the
landed range. Keep original #4 and the redundant stacked candidate unchanged.
Draft #5 remains unresolved and has not landed; no annotation migration or
suppression is proposed.
No Claude, blocked review route, QActivate, settings, remote write, merge or
release.
