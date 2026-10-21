# Goal

Preserve configured Python 3.8 target/API compatibility in original same-org
installer_builder PR #4 without combining its dependency change with the
separate unresolved full-package typing characterization in draft #5.

# State

Local-only repair/task6-installer-mypy-range starts directly at verified actual
merged master 11ec654ac80ef0bd7423156e76a22aa1d8e3a453. It changes the optional
mypy range from >=0.991,<1.0 to >=0.991,<1.15, copies the exact authored
three-case checks/mypy_compatibility.py probe, and invokes it in the existing
Windows Python 3.8 CI leg. Current default tests/build, support >=3.8.6, target
3.8, strict flags, action pins, permissions and every existing step remain.

# Decisions and why

- Original #4 at 62d473dd04ad154d3b4aade2b8723dc76ce73909 proposes <3.0.
  Actual mypy 2.4.0 on tool Python 3.13 replaces the configured 3.8 target after
  warning and accepts the 3.9-only str.removeprefix API. The positive startswith
  control and negative untyped-definition control distinguish target behavior
  from an unloaded configuration. The same three assertions are copied intact.
- Official mypy 1.15 release notes drop tool runtime 3.8. Mypy 1.14.1 declares
  both tool and target minimum 3.8. The <1.15 cap permits that proven endpoint
  without changing the package floor or substituting a newer checker target.
- This explicit target/API/config probe checks generated snippets through the
  public mypy.api.run with the actual project config. It does not check package
  source or establish whole-package typing correctness. It is outside ordinary
  pytest collection, so default mocked tests do not import an optional tool.
- Draft #5 remains open/unmerged and retains its full configured package gate
  on its own branch. Its historical 115 diagnostics are annotation/import/stub
  debt plus separately classified helper issues; they are not suppressed here.
  Current default has no full package gate to remove. This independent change
  does not claim that the separate full-package baseline is green or landed.

# Evidence and limits

Historical focused execution before the true rebases, with isolated dependencies
and --no-project, exercised only this identical authored check file:

- Old <1.0, mypy 0.991 / Python 3.8.20: three passed in 6.924s.
- Original <3.0, mypy 2.4.0 / Python 3.13.15: two failed in 4.350s; target 3.8
  warning requires 3.10 or higher and removeprefix incorrectly returns success.
- Narrowed <1.15, mypy 1.14.1 / Python 3.8.20: three passed in 9.228s.
- Same narrowed range / Python 3.13.15: three passed in 6.305s.

An initial blanket stderr assertion failed the old control because configured
unused override warnings apply to snippet-only checks. The positive assertion
was narrowed to target warnings before the recorded broad-range red/narrowed
greens. No config flag or negative API/strictness assertion was disabled.
Those focused results are historical, not execution at this new branch head.
Hosted execution is pending; no aggregate or full-package-green claim is made.
No local full checker, package install, tests/build or native installer ran.
Actionlint 1.7.12 passed with optional shellcheck/pyflakes disabled. Zizmor
1.31.1 offline pedantic reported no findings. SHA256 of the copied probe and
the preserved stacked probe is identical:
AE3B6AAB59F9B34C92501F8CE0B0DA42B39E66DB32077CFB0FD363FA08EE63A5.

# Preservation

Original #4 remains unchanged in backup/task6-installer-mypy-original-pr.
archive/task6-installer-mypy-baseline-before-11ec retains old 748ddadf;
archive/task6-installer-mypy-compatibility-before-11ec retains old e89bff68.
The genuine rebased baseline 2f18a792 and stacked probe fd0103dc remain intact.
Canonical master 099ceb3 and all canonical dirty/untracked user work are intact.
No remote branch, PR description, settings or model route was changed.

# Next step

Return complete local head/diff and static workflow audits for coordinator
review before any publication. Any hosted probe/test/build green must describe
that exact scope; draft #5's full-package typing characterization stays separate
and unresolved pending its own fresh hosted run. No publication, model or merge.
