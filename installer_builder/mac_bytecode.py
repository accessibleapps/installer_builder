"""Finish py2app bundles as sourceless bytecode using the build interpreter."""
import ast
import copy
import importlib.util
import marshal
from pathlib import Path
import py_compile
from types import CodeType
import zipfile


def _bytecode(code: CodeType) -> bytes:
    return importlib.util.MAGIC_NUMBER + bytes(12) + marshal.dumps(code)


def _compile_archive_sources(archive: Path, optimization: int) -> bool:
    temporary = archive.with_suffix(".bytecode.zip")
    with zipfile.ZipFile(archive) as original:
        sources = {name for name in original.namelist() if name.endswith((".py", ".pyw"))}
        if not sources:
            return False
        compiled = {
            Path(name).with_suffix(".pyc").as_posix(): _bytecode(compile(original.read(name), name, "exec", optimize=optimization))
            for name in sources
        }
        with zipfile.ZipFile(temporary, "w") as result:
            for entry in original.infolist():
                if entry.filename in sources:
                    replacement = copy.copy(entry)
                    replacement.filename = Path(entry.filename).with_suffix(".pyc").as_posix()
                    result.writestr(replacement, compiled[replacement.filename])
                elif entry.filename not in compiled:
                    result.writestr(entry, original.read(entry))
    temporary.replace(archive)
    return True


def compile_bundle_sources(bundle: str, optimization: int) -> bool:
    resources = Path(bundle) / "Contents" / "Resources"
    changed = False
    boot = resources / "__boot__.py"
    if boot.is_file():
        tree = ast.parse(boot.read_text(), filename=str(boot))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "_run":
                # Retain py2app's argv, frozen-runtime and script selection;
                # replace its source-reading branch and execution expression.
                node.body = [statement for statement in node.body if not isinstance(statement, ast.If)]
                node.body[-1] = ast.parse(
                    "exec(__import__('importlib.machinery', fromlist=['SourcelessFileLoader'])"
                    ".SourcelessFileLoader('__main__', path).get_code('__main__'), globals(), globals())"
                ).body[0]
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "DEFAULT_SCRIPT" and isinstance(node.value, ast.Constant):
                        node.value.value = str(Path(node.value.value).with_suffix(".pyc"))
                    if isinstance(target, ast.Name) and target.id == "SCRIPT_MAP" and isinstance(node.value, ast.Dict):
                        for value in node.value.values:
                            if isinstance(value, ast.Constant):
                                value.value = str(Path(value.value).with_suffix(".pyc"))
        code = compile(ast.fix_missing_locations(tree), str(boot), "exec", optimize=optimization)
        boot.with_suffix(".pyc").write_bytes(_bytecode(code))
        boot.unlink()
        changed = True
    for source in sorted(resources.rglob("*")):
        if source.is_file() and source.suffix in (".py", ".pyw"):
            py_compile.compile(str(source), cfile=str(source.with_suffix(".pyc")), doraise=True, optimize=optimization)
            source.unlink()
            changed = True
    for archive in resources.glob("lib/python*.zip"):
        changed = _compile_archive_sources(archive, optimization) or changed
    # Repair this after compiling site.py: py2app emits an optimized-site
    # link before a Python 3-compatible site.pyc target exists.
    for directory in resources.glob("lib/python*"):
        link = directory / "site.pyo"
        if link.is_symlink() and (resources / "site.pyc").is_file():
            link.unlink()
            (link.parent / "site.pyc").symlink_to("../../site.pyc")
            changed = True
    return changed
