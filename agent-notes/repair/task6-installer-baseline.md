# Keep existing mocked tests compatible with Python 3.8

## Goal

Fix only the Python 3.8 grammar failure already on master in the two integration
test files. Replace parenthesized context-manager grouping with equivalent
explicit line continuations, preserving every mock, assertion and call order.
Copy the reviewed Windows 3.8/3.14 full-suite/package workflow for a meaningful
baseline PR gate. No production, support, dependency or new-skip changes.

## State

Origin https://github.com/accessibleapps/installer_builder. New isolated branch
repair/task6-installer-baseline at task-6/worktrees/installer-baseline starts at
fresh master 099ceb30876aba2b853a8bb98815cba3bb19f3e9. Existing draft PR #2 is
published at b57d20b46bab111b41f40115ccbcca22a4b8274a; it is not rewritten here.
Separate backup/task6-installer-builder-local-before-baseline and
backup/task6-installer-builder-published-before-baseline retain that head.
Canonical master, original feature and CI worktrees, all prior backups and
untracked user/environment/history/lock files are preserved.

## Decisions and why

Read global instructions, canonical untracked CLAUDE, all four test modules,
manifest/README, current feature note/report, exact hosted error logs and
reviewed CI. No additional repository/nested guidance. Metadata keeps >=3.8.6.
Hosted PR run 39523522156 failed Python 3.8 collection at test_integration.py:119
and test_new_inno.py:125; Python 3.14 tests/build passed. Both failing syntax
forms are identical on master. Classification: existing test compatibility
defect, not a product defect caused by PR #2.

All 16 parenthesized with blocks (7 legacy, 9 new-command) need conversion,
because collection initially exposes only each file's first incompatible block.
No context expression, as binding, body, expected exception or assertion changes.
The workflow is byte-identical to reviewed PR #2's 43-line ci.yml (SHA256
850A665AA2DFA98E41BD1FBF79DC707E91A7BAA1041728291582E53E9CE06DEA).
It runs existing Windows Python 3.8/3.14 tests, nonpublishing uv build and checks
both package artifacts. No compiler, freezer, signer or release invocation.

## Verification and surprises

Actual fresh-master focused red: uv 0.13.4 run --python 3.8 pytest
test_integration.py test_new_inno.py -q --tb=short reported the exact two
SyntaxErrors, 2 collection errors in 0.83 s, CPython 3.8.20.
Same focused command after fix: 47 passed, 3 existing warnings, 2.34 s.
Modern-parser AST comparison against both original master files returned True
for both complete files, proving all executable test structure is preserved.
That parser was existing CPython 3.14.0rc1; it was used only for the structural
comparison, not as a claimed stable Python 3.14 test run.
Actionlint 1.7.12 passed (optional shellcheck/pyflakes disabled); zizmor 1.31.1
offline pedantic reported no findings. CRLF-aware diff check passed.
No local full suite/build CI rerun. Generated isolated env, caches and uv.lock
stay untracked/excluded. No tracked lock or dependency graph was changed.

## Next step

Return the committed local baseline diff/head for coordinator review before any
new publication. Hosted full-suite/build results for this new baseline and
actual Claude review remain pending separate authorization. Do not push, alter
PR descriptions/settings, merge or rebase feature #2 under this local scope.
