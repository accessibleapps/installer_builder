# Keep the existing Dependabot proposal with a relevant CI gate

## Goal

Prepare existing Installer Builder PR #1 on the actual landed baseline. Keep the
original seven-line config unchanged; validate its schema in the existing 3.14
CI leg. No new runtime axis, source, dependency, support or setting changes.

## State

Origin https://github.com/accessibleapps/installer_builder. Baseline PR #3 merged
as squash 8f5d7f28381066ec3bafac95468e3d7970261d58 after actual review and full
Windows 3.8/3.14 tests/build. Fresh remote master is that exact commit, whose
file tree equals old baseline e45937f8a16565e0160621b956d3b5fb3bb9aefe.
Open non-draft PR #1, dependabot/add-v2-config-file, remains at
50f710fe75c412dea43186007c5b50af2516ce10. No replacement config exists on master.

Local repair/task6-installer-dependabot-successor was genuinely rebased using
--no-update-refs --onto 8f5d7f2 e45937f. Old local stack
8bc43f6a93a1c5e2ab783b886c7d0c34e1ec8097 and exact published tip have separate
before-landed-rebase backups. Original branches, canonical master 099ceb3,
dirty/untracked user work and all previous archives remain untouched.
No remote update. No local branch existed for original Dependabot head; only
this authorized isolated successor was rebased.

## Decisions and why

The prior inspected stack merged original config onto e45937f and authored the
schema step/note in its merge commit. Ordinary rebase replays the config commit
but omits merge-authored edits. Restore exactly the already approved three-line
CI step and this same living-note path; do not lose them or substitute new CI.
The final config and workflow are byte-identical to the accepted old stack.

Existing version:2, pip, directory:/, daily interval and open limit10 remain
valid. Historical focused check-jsonschema 0.38.2 builtin vendor.dependabot audit
returned "ok -- validation done" on the unchanged file. This proves schema shape,
not future scheduling/network/private Git access. No service/settings calls.
The tool requires Python >=3.10, so validation stays only in the existing 3.14
leg while the full 3.8/3.14 suite/build remains. Package support stays >=3.8.6.
Historical actionlint 1.7.12 and zizmor 1.31.1 offline/pedantic audits passed for
this identical workflow. No local full CI or audit repetition was performed.

## Surprises

The landed squash has the same tree as e45937f but a different commit identity;
the actual landed master is the required new ancestor. Global rebase.updateRefs
is true, so explicit --no-update-refs protects all backup/original refs.
Inherited baseline green does not establish this unpublished head's hosted result.

## Next step

Return complete local head/diff for coordinator review before publication.
Recapture exact live default/PR tips and obtain guarded publication authority;
then require full final-head hosted schema/tests/build and actual review before
merge. No close, description, model, settings, release or remote merge action.
