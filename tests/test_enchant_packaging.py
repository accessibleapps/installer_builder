import os
import sys
from types import SimpleNamespace

import pytest

from installer_builder import InstallerBuilder, hook_enchant


@pytest.mark.parametrize("maxsize, architecture", [(2 ** 63 - 1, "mingw64"), (2 ** 31 - 1, "mingw32")])
def test_bootcode_locates_collected_native_runtime_beside_executable(tmp_path, monkeypatch, maxsize, architecture):
    package = tmp_path / "installed" / "enchant"
    source_library = package / "data" / architecture / "bin" / "libenchant-2.dll"
    source_library.parent.mkdir(parents=True)
    source_library.write_bytes(b"native library fixture")
    collected_prefix = tmp_path / "frozen" / "data" / architecture
    collected_library = collected_prefix / "bin" / source_library.name
    collected_library.parent.mkdir(parents=True)
    collected_library.write_bytes(source_library.read_bytes())
    bootcode = []
    monkeypatch.setattr(sys, "maxsize", maxsize)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "frozen" / "QSeek.exe"))
    monkeypatch.setenv("PYENCHANT_ENCHANT_PREFIX", "")
    monkeypatch.setenv("PYENCHANT_LIBRARY_PATH", "")

    hook_enchant(
        SimpleNamespace(add_bootcode=bootcode.append),
        SimpleNamespace(__path__=[str(package)]),
    )
    assert len(bootcode) == 1
    exec(compile(bootcode[0], "<enchant bootcode>", "exec"), {})

    assert os.environ["PYENCHANT_ENCHANT_PREFIX"] == str(collected_prefix)
    assert (collected_prefix / "bin" / "libenchant-2.dll").is_file()


@pytest.mark.parametrize("override", ["PYENCHANT_ENCHANT_PREFIX", "PYENCHANT_LIBRARY_PATH"])
def test_bootcode_preserves_the_loaders_existing_override(tmp_path, monkeypatch, override):
    package = tmp_path / "enchant"
    architecture = "mingw64" if sys.maxsize > 2 ** 32 else "mingw32"
    library = package / "data" / architecture / "bin" / "libenchant-2.dll"
    library.parent.mkdir(parents=True)
    library.write_bytes(b"native library fixture")
    collected_library = tmp_path / "frozen" / "data" / architecture / "bin" / library.name
    collected_library.parent.mkdir(parents=True)
    collected_library.write_bytes(library.read_bytes())
    monkeypatch.setattr(sys, "executable", str(tmp_path / "frozen" / "QSeek.exe"))
    monkeypatch.delenv("PYENCHANT_ENCHANT_PREFIX", raising=False)
    monkeypatch.delenv("PYENCHANT_LIBRARY_PATH", raising=False)
    monkeypatch.setenv(override, "existing user choice")
    expected = {key: os.environ.get(key) for key in ("PYENCHANT_ENCHANT_PREFIX", "PYENCHANT_LIBRARY_PATH")}
    bootcode = []

    hook_enchant(SimpleNamespace(add_bootcode=bootcode.append), SimpleNamespace(__path__=[str(package)]))
    exec(compile(bootcode[0], "<enchant bootcode>", "exec"), {})

    assert {key: os.environ.get(key) for key in expected} == expected


def test_bootcode_keeps_system_discovery_when_native_data_was_not_collected(tmp_path, monkeypatch):
    architecture = "mingw64" if sys.maxsize > 2 ** 32 else "mingw32"
    package = tmp_path / "enchant"
    library = package / "data" / architecture / "bin" / "libenchant-2.dll"
    library.parent.mkdir(parents=True)
    library.write_bytes(b"native library fixture")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "without-data" / "QSeek.exe"))
    monkeypatch.setenv("PYENCHANT_ENCHANT_PREFIX", "")
    monkeypatch.setenv("PYENCHANT_LIBRARY_PATH", "")
    bootcode = []

    hook_enchant(SimpleNamespace(add_bootcode=bootcode.append), SimpleNamespace(__path__=[str(package)]))
    exec(compile(bootcode[0], "<enchant bootcode>", "exec"), {})

    assert os.environ["PYENCHANT_ENCHANT_PREFIX"] == ""


def test_legacy_layout_does_not_install_a_mingw_prefix(tmp_path):
    bootcode = []
    hook_enchant(SimpleNamespace(add_bootcode=bootcode.append), SimpleNamespace(__path__=[str(tmp_path)]))
    assert bootcode == []


def test_enchant_hook_is_registered_before_freezing(monkeypatch):
    import py2exe
    import py2exe.hooks

    calls = []

    def freeze(**kwargs):
        assert py2exe.hooks.hook_enchant is hook_enchant
        calls.append(kwargs)

    monkeypatch.setattr(py2exe, "freeze", freeze)
    monkeypatch.setattr(sys, "argv", ["setup.py", "py2exe"])
    builder = InstallerBuilder(
        main_module="main.pyw", name="Enchant packaging", version="1.0.0", author="Accessible Apps",
    )
    builder.build_installer()
    assert len(calls) == 1
