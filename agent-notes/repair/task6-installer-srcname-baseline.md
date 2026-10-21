# Repair legacy Inno Setup source and directory helpers

## Goal

Fix two confirmed baseline compatibility defects in the existing legacy module:
use the string values in importlib.machinery.SOURCE_SUFFIXES directly, and use
the distribution directory saved by InnoScript's constructor. Three production
lines change; one focused regression file loads the real production module.

## State

Isolated branch repair/task6-installer-srcname-baseline at
task-6/worktrees/installer-srcname-baseline starts at exact merged default
e59336b7b5acb88d76d829dc9b61ac6585ba189d. Origin is
https://github.com/accessibleapps/installer_builder. Canonical master 099ceb308
and its untracked user work, all archived/original tips, and other worktrees
remain untouched. The separate mypy worker's branches and source are not edited.
No remote actions or model calls are part of this local preparation.

## Decisions and why

Read global instructions, canonical untracked CLAUDE, exact baseline source,
manifest, README, hosted workflow, relevant existing fixtures and living notes.
No repository AGENTS or .agents directory was found. Existing CI authority is
the unchanged complete Windows Python 3.8/3.14 pytest suite and package build.

srcname accepts a module or dotted module name; srcnames forwards directly to it.
Real json/json.decoder modules and the real standard-library SOURCE_SUFFIXES
reach the string.suffix AttributeError. The module's changelog names these public
helpers, but no current internal builder caller was found: this is not a claim
that the normal installer command fails. Preserve source-sibling fallback and
the existing missing-source ValueError.

InnoScript.__init__ stores self.dist_dir, never self.builder. The legacy
innosetup.run creates this object and calls create, whose Setup handler reads
self.builder.dist_dir; chop has the same stale access. Both now read self.dist_dir.
The main InstallerBuilder uses NewInnoSetupCommand; do not describe this legacy
path defect as a normal installer outage. No compiler or signer behavior changes.

The fixture executes the real innosetup.py through importlib, with a private
temporary package name and empty native/freezer/signing module stubs. Registry
constants are inert objects. monkeypatch restores every replaced sys.modules
entry and distutils.command.__all__, including the legacy registration alias.
No copied helper implementation or AST extraction is used. Constructor tests
only scan pytest's temporary directory and render the Setup section in memory.

## Verification and surprises

Focused command (only the actively authored regression file):
task-6/worktrees/installer-baseline/.venv/Scripts/python.exe -m pytest
tests/test_innosetup_srcname.py -q --tb=short

Existing interpreter: CPython 3.8.20, pytest 8.3.5. Before any production fix,
all seven source-helper cases failed at line 306 with
AttributeError: 'str' object has no attribute 'suffix' (0.99 s).
After the one-line source fix, those same seven passed (0.64 s).
The two added directory cases then failed at lines 525/691 with
AttributeError: 'InnoScript' object has no attribute 'builder', while all seven
controls stayed green (0.68 s). After the two directory fixes, the unchanged
nine cases passed (0.44 s). Two existing invalid-escape deprecation warnings
were reported; none were suppressed. No full suite, build, mypy, compiler,
freezer, signing, registry API, network or native-resource action ran.

The production file retains its existing CRLF line endings; whitespace checking
uses git's cr-at-eol setting. The patch changes no support/dependency metadata,
workflow, existing assertions or configuration. No new skip or policy is added.

## Next step

Return the committed complete local diff/head and focused red/green evidence
for coordinator review before publication. Root owns any new draft, actual
hosted full matrix/build, Claude review, gate and merge. Those results are not
claimed by this focused local check. Keep all unrelated branches untouched.
