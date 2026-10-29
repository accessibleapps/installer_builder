from pathlib import Path
import os
import shutil
import subprocess
import sys

from installer_builder.mac_bytecode import compile_bundle_sources


def test_archive_sources_replace_existing_bytecode_and_import(tmp_path):
    import zipfile
    bundle = tmp_path / "QCast.app"
    library = bundle / "Contents" / "Resources" / "lib"
    library.mkdir(parents=True)
    archive = library / "python311.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("package/__init__.py", "")
        output.writestr("package/main.py", "value = 'compiled archive'\n")
        output.writestr("package/main.pyc", b"obsolete bytecode")
    assert compile_bundle_sources(str(bundle), 1)
    with zipfile.ZipFile(archive) as result:
        assert len(result.namelist()) == len(set(result.namelist()))
        assert not any(name.endswith(".py") for name in result.namelist())
    process = subprocess.run([
        sys.executable, "-c", "import sys; sys.path.insert(0,sys.argv[1]); from package.main import value; print(value)", str(archive),
    ], capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert process.stdout.strip() == "compiled archive"


def test_compiled_boot_executes_main_and_sourceless_package(tmp_path):
    import json
    import py_compile

    bundle = tmp_path / "QCast.app"
    resources = bundle / "Contents" / "Resources"
    package = resources / "gui"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("value = 'sourceless GUI'\n")
    observed = json.loads((Path(__file__).parent / "fixtures" / "py2app_cached_bytecode.json").read_text())
    cache = package / "__pycache__" / "__init__.cpython-311.pyc"
    cache.parent.mkdir()
    py_compile.compile(str(package / "__init__.py"), cfile=str(cache), doraise=True)
    cache.write_bytes(bytes.fromhex(observed["header_hex"]) + cache.read_bytes()[16:])
    (resources / "main.pyw").write_text("import gui; print(gui.value)\n")
    shutil.copyfile(Path(__file__).parent / "fixtures" / "py2app_boot.py", resources / "__boot__.py")

    assert compile_bundle_sources(str(bundle), 1)

    assert not list(resources.rglob("*.py"))
    assert not list(resources.rglob("*.pyw"))
    assert not list(resources.rglob("__pycache__"))
    environment = dict(os.environ, RESOURCEPATH=str(resources), ARGVZERO="QCast")
    result = subprocess.run([sys.executable, str(resources / "__boot__.pyc")], env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "sourceless GUI"
