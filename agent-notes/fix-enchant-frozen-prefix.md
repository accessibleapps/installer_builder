# Repair frozen Enchant and curl_cffi native discovery

## Goal

Repair the shared Enchant collector/runtime contract exposed by QSeek's frozen app, following Q's direction to use sibling/shared packaging solutions.

The same native dependency investigation also identifies curl_cffi's vendored libcurl DLL, present in its source wheel's curl_cffi.libs but absent from the frozen artifact. The PE imports of the actual packaged wrapper name that DLL. The shared hook uses finder.add_dll for actual bundled DLLs, following the existing py2exe NumPy/Matplotlib wheel hooks. This adds about six source lines plus focused collection/registration tests, without changing HTTP or TLS behavior. The Enchant worker owns only the prefix hook; root owns the separate curl hook.

## State

Independent fix/enchant-frozen-prefix branch starts at current integrated installer_builder master after PR #14. Canonical sibling changes and the separate chardet worktree are preserved. QSeek's collector places Enchant DLLs and dictionaries under data/mingw64; archived enchant._enchant searches relative to library.zip/enchant and cannot find them. Isolated imports from the actual artifact fail normally, then succeed with a per-process PYENCHANT_ENCHANT_PREFIX pointing to the collected data: 22 dictionaries and a successful English word check. No artifact was modified. The shared Enchant hook and registration are now implemented. Seven authored-file tests pass using QSeek's current Python with this owner source first on the import path; no broad local suite, typecheck or build was run.

## Decisions and why

Both source repairs are implemented. Seven authored Enchant bootcode tests and three authored curl_cffi collection tests pass. Root independently read the actual Enchant loader and curl_cffi wheel patch, confirmed the missing libcurl name from the packaged wrapper's PE imports, and compared the existing py2exe NumPy/Matplotlib add_dll mechanism. No complete local CI or frozen build was run; hosted owner CI is next.

Use the owner's existing py2exe hook/add_bootcode contract, roughly 15 source lines plus focused tests. For the current MinGW package layout, set the runtime prefix to the collected directory before importing Enchant, using executable-relative paths and the target interpreter architecture. Preserve existing PYENCHANT_ENCHANT_PREFIX and PYENCHANT_LIBRARY_PATH choices because the actual loader honors them. Older layouts without the matching data prefix must remain unchanged. No product-local environment workaround, data relocation, native disablement or dependency pin. Chardet's integrated hook remains unchanged.

## Surprises

The library and all dictionaries are already collected; discovery is the defect. This repair does not need more DLLs or duplicate resource collection. Source-mode Enchant works because its resources are beside the source package, whereas the frozen module lives in library.zip.

## Next step

Root reviews and publishes the shared repair, then reads CI/review before its merge decision. Enchant's bootcode uses the executable-relative collected prefix only when its DLL exists and neither explicit loader override is selected. Tests execute that bootcode for both target architectures and retain system fallback if no native payload was collected. These are bootcode/collection contract tests, not proof of native frozen startup. QSeek consumes only integrated owner code, then retries the actual downloaded app. No release, install, activation, signing or debug-listener changes are part of this repair. Root separately owns the curl_cffi native dependency hook in this branch; the Enchant worker did not edit that hook or its test.
