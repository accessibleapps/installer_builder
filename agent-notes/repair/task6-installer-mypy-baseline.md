# Goal

Resolve the full configured installer_builder typing baseline after the bounded
range/target compatibility change landed separately in #7. Preserve package
>=3.8.6, mypy target 3.8, public behavior and every existing strict setting.

# State

Published PR #5 remains open and unmerged, with full typing work remaining.
repair/task6-installer-mypy-baseline was genuinely rebased onto merged master
fad12d9a3eafa59fcd6033e54534c4eee3ed2fb7 using --no-update-refs. The last
recorded completed measurement is run 39563222831 at published source head
bbf7a823aab11ea59728e580217d5c0f81d7aafb, detailed below. Live PR checks are
authoritative for later heads; that measurement is not a promised later result.
The baseline gate remains unchanged in the existing Windows Python 3.8 leg.
The merged base supplies mypy>=0.991,<1.15 and the unchanged three-case
target/API/config probes on tool Python 3.8 and 3.13. The authorized source
repair now annotates the four production modules and adds only the proven
Python 3.8-compatible types-setuptools development stub. The completed first
annotation measurement remains the last recorded result; no green result is inferred for
this source candidate. No full package checker command has run locally.

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
  The latest recorded run 39563222831 at bbf7a823 established the diagnostic
  snapshot detailed in Verification below.
- The existing Windows 3.8/3.14 test/build axes, check names, action pins,
  permissions, checkout credentials policy, timeout and concurrency remain.
  A failing baseline step prevents that leg's later build in the usual way;
  it is not a green baseline and does not justify suppressing the failure.
- The landed compatibility probes and dependency narrowing are separate source
  intent, now inherited once each from actual master. Those green bounded
  config/target/API probes are not full-package typecheck evidence. The rebase
  resolved one adjacent-step workflow conflict by keeping both unchanged probes
  followed by exactly one existing full-package command; no other hunk changed.

# Typing repair decisions and actual boundaries

- Annotate all 89 previously reported definitions and the six untyped container
  sites with Python 3.8 typing forms: concrete string collections, data-file
  tuples, generators, paths, optional lifecycle state and return types. Keep
  implicit None fallthroughs explicit without adding new fallback values.
- Path aliases quote os.PathLike[str] so alias evaluation does not require
  Python 3.9 runtime generics. Actual os/path-only input surfaces accept string
  or PathLike paths; legacy chop/dist_dir operations still require strings.
  Application.name is a read-only protocol property; srcname accepts modules,
  dotted strings and the existing __file__ duck-typed input. InnoScript metadata
  is object because it is inspected with dir/getattr and existing tests supply
  SimpleNamespace, not only DistributionMetadata.
- Command dist_dir remains Optional during initialize_options. The narrow
  casts at run/signing use the real distutils lifecycle: Distribution.run_command
  calls ensure_finalized before run, and each finalize_options supplies dist.
  Direct invalid calls retain their old failures; no new runtime guard is added.
  Likewise build() sets build_start_time before both reporting paths and calls
  build_installer's existing name validation before finalization. Casts express
  those cross-method facts without changing initialization or validation.
- Keep Any only at actual external dynamic boundaries: extensible setuptools/
  py2exe keyword dictionaries, forwarded application **kwargs, public metadata
  dir/getattr values and native registry values/defaults. Internal file lists,
  command options, translations, script lines and generated metadata are typed.
- Optional Babel/pytz/certifi/enchant helpers consume only package __path__ or
  __file__, not provider APIs. Use the existing importlib.import_module pattern
  and stdlib module metadata types. Each real import still executes at the same
  feature point and fails normally when absent; no provider or native Enchant
  installation is added solely to satisfy a checker. File-backed provider path
  casts retain the same invalid-metadata failures rather than inventing paths.
- Add types-setuptools==75.8.0.20250110 only to the existing optional dev extra.
  Its official PyPI metadata requires >=3.8, has no dependencies and records
  testing with mypy 1.14.1. It types actual setup/find_packages APIs; no runtime
  dependency, mypy option, ignored module, coverage or workflow is weakened.
  On supported Python >=3.8, import builtins directly under the existing alias
  rather than probing the obsolete Python 2 __builtin__ module.
- No runtime defect was established in this repair. The small executable edits
  are import spelling, identity casts, local variable separation for registry
  root names/handles, and explicit existing None fallthroughs. No new signing,
  build, compiler, native, data-generation or optional-feature policy is added.
- First hosted annotation feedback left six errors. Remove the now-proven
  redundant dottedname cast and spell the three existing bare returns as None.
  DistributionMetadata name/version are genuinely nullable; do not cast away
  that state or use getters that invent UNKNOWN/0.0.0. At the final join boundary
  explicitly narrow both captured values to str, retaining TypeError for invalid
  values with join's existing sequence-item/type-name message. Valid string
  metadata comes from the existing Distribution producer in test_new_inno.py;
  the type checks preserve the accepted input set instead of asserting that
  every Distribution always has valid metadata. This exposes the existing
  string-join contract without a new runtime feature or a suppression.

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
or forced through duplicate conflicts. The PR #4 branch was not modified by
this task. Dependabot independently refreshed it to
995f935b95fbe64004cb47fc779af9f13a589e3a with <2.5 after #7; coordinator
verified run 39554719205 fails two 3.13 probe cases with mypy 2.4. The original
62d473dd archive remains preserved; no result for that separate head is implied
by this #5 source repair.
These earlier archive tips are historical. Named
archive/task6-installer-mypy-baseline-measurement-cde0f5c8 preserves the exact
cde0f5c85b442e727583f06a6eeec352eaa0003a measured tip before this note correction.
archive/task6-installer-mypy-baseline-before-typing preserves exact
76332cebdb1eaac1400427daf73b3b4bafd87b6c before these source annotations.
archive/task6-installer-mypy-baseline-first-typing-bbf7a82 preserves exact
bbf7a823aab11ea59728e580217d5c0f81d7aafb before the focused six-error follow-up.

# Verification

Historically, actionlint 1.7.12 passed with optional shellcheck/pyflakes disabled
and zizmor 1.31.1 offline pedantic reported no findings for the unchanged added
workflow step. Hosted run 39548810883 at old head 748ddadf failed the full
configured package check with 115 errors in four files using the existing <1.0
tool; its Python 3.14 tests/build passed. The next published baseline 2f18a792
had 112 diagnostics with mypy 0.991 in run 39552363115 after the three helper
diagnostics disappeared; both 71-test suites passed. These are historical
results under the old <1.0 range. Actual #7
landed the narrower compatible <1.15 range and bounded probes separately.
The historical pre-annotation measurement, run 39555011151 at exact cde0f5c8,
selected mypy 1.14.1 and failed with 106 errors in four package files.
Diagnostic classes: 89 no-untyped-def, 6 var-annotated, 3 import-untyped,
3 import-not-found, 3 arg-type, 1 assignment and 1 operator.
Both 71-test suites passed, as did all three compatibility cases on tool Python 3.8
and 3.13. The Python 3.8 build was skipped after the full-check failure; the
Python 3.14 build succeeded. This remains a red full-package baseline. Actual
review approved the workflow source hunk and requested only this stale-note
correction. No local full checker, tests/build or installer/signing action ran,
including for this note-only correction.
At the recorded cde measurement, delta inspection confirmed the same three-line
unsuppressed gate without source/test/manifest/probe/strict-setting changes.
After resolving the adjacent-step conflict, actionlint 1.7.12 again exited 0
and offline pedantic zizmor 1.31.1 reported no findings. No local test or
checker execution was added to that static workflow verification.

For this source candidate, every existing production definition was inspected
and annotated, including all reported no-untyped-def/container sites. Known
import complaints are addressed through the real setuptools stub, supported
builtins import and module-path boundaries. Optional path/timing/platform
assignments are typed according to their actual lifecycles. This is an estimate
of addressed source sites, not a checker result or count prediction: newly
exposed precise-type diagnostics may need hosted feedback. No local checker,
tests/build, optional provider import or native action ran. No regression was
added merely to mirror annotations; existing 71 tests and both three-case
compatibility probes remain intact. The workflow is byte-for-byte unchanged.

Last recorded completed source measurement on 2026-10-21: run 39563222831 at
exact bbf7a823aab11ea59728e580217d5c0f81d7aafb. Both 71-test suites passed;
all three probe cases passed with mypy 1.14.1 on Python 3.8.20 and 3.13.16.
The Python 3.14 build passed; the full checker remained red with six errors in
two files (two list-item, one redundant-cast, three return-value). Python 3.8
build was skipped after that failure. The focused follow-up addresses those
exact six source sites; its result must come from the next hosted run. No
local checker, tests/build, provider import, signing or native action ran.

# Next step

Return this focused two-source-file/note follow-up for coordinator review
before guarded publication and the next hosted full-package measurement.
Resolve any remaining accurate-type diagnostics under the unchanged full gate;
do not suppress, weaken flags or shrink coverage. Keep original #4, the redundant
stacked candidate and canonical work unchanged. PR #5 remains open/unmerged;
no merge until the relevant full check is green and source review is complete.
Live checks govern later heads. No model, remote write or merge ran here.
