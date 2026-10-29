from pathlib import Path
import os
import shutil
import subprocess
import sys

from installer_builder.mac_bytecode import compile_bundle_sources


def test_compiled_boot_executes_main_and_sourceless_package(tmp_path):
    bundle = tmp_path / "QCast.app"
    resources = bundle / "Contents" / "Resources"
    package = resources / "gui"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("value = 'sourceless GUI'\n")
    (resources / "main.pyw").write_text("import gui; print(gui.value)\n")
    shutil.copyfile(Path(__file__).parent / "fixtures" / "py2app_boot.py", resources / "__boot__.py")

    assert compile_bundle_sources(str(bundle), 1)

    assert not list(resources.rglob("*.py"))
    assert not list(resources.rglob("*.pyw"))
    environment = dict(os.environ, RESOURCEPATH=str(resources), ARGVZERO="QCast")
    result = subprocess.run([sys.executable, str(resources / "__boot__.pyc")], env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "sourceless GUI"
