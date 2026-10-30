import sys
from types import SimpleNamespace

from installer_builder import InstallerBuilder, hook_curl_cffi


def test_collects_the_native_wheel_libraries_from_the_sibling_directory(tmp_path):
    package = tmp_path / "curl_cffi"
    package.mkdir()
    libraries = tmp_path / "curl_cffi.libs"
    libraries.mkdir()
    library = libraries / "libcurl-impersonate-vendor.dll"
    library.write_bytes(b"native wheel dependency")
    (libraries / "README.txt").write_text("not a DLL", encoding="utf-8")
    collected = []

    hook_curl_cffi(SimpleNamespace(add_dll=collected.append), SimpleNamespace(__path__=[str(package)]))

    assert collected == [str(library)]


def test_older_wheel_without_a_sibling_dll_directory_is_unchanged(tmp_path):
    collected = []
    hook_curl_cffi(SimpleNamespace(add_dll=collected.append), SimpleNamespace(__path__=[str(tmp_path / "curl_cffi")]))
    assert collected == []


def test_curl_hook_is_registered_before_freezing(monkeypatch):
    import py2exe
    import py2exe.hooks

    calls = []

    def freeze(**kwargs):
        assert py2exe.hooks.hook_curl_cffi is hook_curl_cffi
        calls.append(kwargs)

    monkeypatch.setattr(py2exe, "freeze", freeze)
    monkeypatch.setattr(sys, "argv", ["setup.py", "py2exe"])
    InstallerBuilder(main_module="main.pyw", name="Curl packaging", version="1.0.0", author="Accessible Apps").build_installer()
    assert len(calls) == 1
