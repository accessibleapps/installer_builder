import distutils.command
import importlib.util
import io
import json
import json.decoder
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def innosetup_module(monkeypatch):
    # Load the real legacy module without importing native packaging/signing code.
    package_name = "_installer_srcname_test"
    package = ModuleType(package_name)
    package.__path__ = []
    monkeypatch.setitem(sys.modules, package_name, package)
    for name in (package_name + ".signtool", "win32api", "py2exe"):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    registry = ModuleType("winreg")
    for name in (
        "HKEY_LOCAL_MACHINE", "HKEY_CURRENT_USER", "HKEY_CLASSES_ROOT",
        "HKEY_USERS", "HKEY_CURRENT_CONFIG", "HKEY_PERFORMANCE_DATA",
    ):
        setattr(registry, name, object())
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(distutils.command, "__all__", list(distutils.command.__all__))
    monkeypatch.setitem(
        sys.modules, "distutils.command.innosetup", ModuleType("innosetup")
    )
    source = Path(__file__).resolve().parents[1] / "installer_builder" / "innosetup.py"
    spec = importlib.util.spec_from_file_location(package_name + ".innosetup", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("module", [json, json.decoder])
@pytest.mark.parametrize("use_name", [False, True])
def test_srcname_finds_real_standard_library_source(innosetup_module, module, use_name):
    argument = module.__name__ if use_name else module

    assert innosetup_module.srcname(argument) == module.__file__
    assert Path(module.__file__).is_file()


def test_srcnames_accepts_modules_and_dotted_names(innosetup_module):
    assert innosetup_module.srcnames(json, "json.decoder") == [
        json.__file__, json.decoder.__file__
    ]


def test_srcname_falls_back_to_existing_source_sibling(innosetup_module, monkeypatch):
    source = json.__file__
    monkeypatch.setattr(json, "__file__", str(Path(source).with_suffix(".pyc")))

    assert innosetup_module.srcname(json) == source


def test_srcname_preserves_missing_source_error(innosetup_module, tmp_path):
    module = SimpleNamespace(__file__=str(tmp_path / "missing.pyc"))

    with pytest.raises(ValueError, match="^Source file not found for "):
        innosetup_module.srcname(module)


def test_chop_uses_constructor_distribution_directory(innosetup_module, tmp_path):
    script = innosetup_module.InnoScript(str(tmp_path), SimpleNamespace(), "")

    assert script.chop(str(tmp_path / "app.py")) == "app.py"


def test_setup_handler_uses_constructor_output_directory(innosetup_module, tmp_path):
    metadata = SimpleNamespace(
        name="Test App", version="1.0", author_email="", url="",
        author="", copyright="", description="",
    )
    script = innosetup_module.InnoScript(str(tmp_path), metadata, "")
    output = io.StringIO()

    script.handle_iss_setup([], output)

    assert script.iss_metadata["OutputDir"] == str(tmp_path)
    assert "OutputDir=%s\n" % tmp_path in output.getvalue()
