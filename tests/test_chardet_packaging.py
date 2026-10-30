import importlib
import importlib.machinery
import importlib.resources
import sys
from types import SimpleNamespace
from zipfile import ZipFile

from py2exe.dllfinder import ModuleFinder

from installer_builder import InstallerBuilder, hook_chardet


MODEL_NAMES = ("confusion.bin", "idf.bin", "langnorm.bin", "models.bin", "rowmax.bin")


def test_compiled_helpers_and_models_are_available_at_the_frozen_boundary(tmp_path, monkeypatch):
    package = tmp_path / "chardet"
    extension = importlib.machinery.EXTENSION_SUFFIXES[0]
    members = [
        "__init__.py", "_kernel" + extension,
        "pipeline/__init__.py", "pipeline/orchestrator" + extension,
        "pipeline/orchestrator__mypyc" + extension,
        "pipeline/ascii" + extension, "pipeline/ascii__mypyc" + extension,
        "models/__init__.py", "models/_format" + extension,
        "models/_format__mypyc" + extension, "models/training_metadata.yaml",
    ]
    for name in members:
        target = package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"")
    for name in MODEL_NAMES:
        (package / "models" / name).write_bytes(name.encode("ascii"))
    queued, resources = [], {}
    finder = SimpleNamespace(
        import_package_later=queued.append,
        add_datafile_to_zip=resources.__setitem__,
    )

    hook_chardet(finder, SimpleNamespace(__name__="chardet", __path__=[str(package)]))

    # Use the real finder's immediate-member discovery, including native suffixes.
    native_finder = ModuleFinder()
    collected = {
        name + "." + child
        for name in queued
        for child in native_finder.find_all_submodules(
            SimpleNamespace(__path__=[str(package.joinpath(*name.split(".")[1:]))])
        )
    }
    assert {
        "chardet._kernel", "chardet.pipeline.orchestrator__mypyc",
        "chardet.pipeline.ascii__mypyc", "chardet.models._format__mypyc",
    } <= collected
    assert set(resources) == {"chardet/models/" + name for name in MODEL_NAMES}

    archive = tmp_path / "library.zip"
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("chardet/__init__.py", "")
        bundle.writestr("chardet/models/__init__.py", "")
        for destination, source in resources.items():
            bundle.write(source, destination)
    for name in list(sys.modules):
        if name == "chardet" or name.startswith("chardet."):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.syspath_prepend(str(archive))
    importlib.invalidate_caches()
    try:
        for name in MODEL_NAMES:
            if hasattr(importlib.resources, "files"):
                data = importlib.resources.files("chardet.models").joinpath(name).read_bytes()
            else:
                data = importlib.resources.read_binary("chardet.models", name)
            assert data == name.encode("ascii")
    finally:
        for name in list(sys.modules):
            if name == "chardet" or name.startswith("chardet."):
                sys.modules.pop(name)


def test_legacy_layout_does_not_request_nonexistent_subpackages(tmp_path):
    queued, resources = [], {}
    hook_chardet(
        SimpleNamespace(import_package_later=queued.append, add_datafile_to_zip=resources.__setitem__),
        SimpleNamespace(__name__="chardet", __path__=[str(tmp_path)]),
    )
    assert queued == ["chardet"]
    assert resources == {}


def test_chardet_hook_is_registered_before_the_freezer_runs(monkeypatch):
    import py2exe
    import py2exe.hooks

    calls = []

    def freeze(**kwargs):
        assert py2exe.hooks.hook_chardet is hook_chardet
        calls.append(kwargs)

    monkeypatch.setattr(py2exe, "freeze", freeze)
    monkeypatch.setattr(sys, "argv", ["setup.py", "py2exe"])
    builder = InstallerBuilder(
        main_module="main.pyw", name="Chardet packaging", version="1.0.0", author="Accessible Apps",
    )
    builder.build_installer()
    assert len(calls) == 1
