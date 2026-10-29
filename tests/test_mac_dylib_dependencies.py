import subprocess
from unittest.mock import Mock

import pytest

from installer_builder import InstallerBuilder


def test_bundled_opus_dependency_uses_its_sibling_bass(tmp_path, monkeypatch):
    builder = InstallerBuilder(name="QCast", main_module="main.pyw")
    builder.dist_dir = str(tmp_path)
    bundle = tmp_path / "QCast.app"
    libraries = bundle / "Contents" / "Resources" / "sound_lib" / "lib" / "x64"
    libraries.mkdir(parents=True)
    (libraries / "libbass.dylib").touch()
    opus = libraries / "libbassopus.dylib"
    opus.touch()
    monkeypatch.setattr(
        subprocess, "check_output",
        lambda args, **kwargs: (
            "\t@rpath/libbass.dylib (compatibility version 1.0.0)\n"
            "\t@rpath/external.dylib (compatibility version 1.0.0)\n"
            "\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0)\n"
        ) if args[-1] == str(opus) else "",
    )
    calls = Mock()
    monkeypatch.setattr(subprocess, "check_call", calls)
    signer = Mock()
    import sys
    from types import SimpleNamespace
    monkeypatch.setitem(sys.modules, "py2app.util", SimpleNamespace(codesign_adhoc=signer))

    builder.repair_mac_dylib_dependencies()

    assert calls.call_args_list[0].args[0] == [
        "install_name_tool", "-change", "@rpath/libbass.dylib",
        "@loader_path/libbass.dylib", str(opus),
    ]
    assert calls.call_count == 2
    signer.assert_called_once_with(str(bundle))
    assert calls.call_args.args[0] == ["codesign", "--verify", "--deep", "--strict", str(bundle)]


def test_failed_dependency_rewrite_stops_build(tmp_path, monkeypatch):
    builder = InstallerBuilder(name="QCast", main_module="main.pyw")
    builder.dist_dir = str(tmp_path)
    libraries = tmp_path / "QCast.app"
    libraries.mkdir()
    for name in ("libbass.dylib", "libbassopus.dylib"):
        (libraries / name).touch()
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: "\t@rpath/libbass.dylib (compatibility version 1.0.0)")
    monkeypatch.setattr(subprocess, "check_call", Mock(side_effect=subprocess.CalledProcessError(1, "install_name_tool")))

    with pytest.raises(subprocess.CalledProcessError):
        builder.repair_mac_dylib_dependencies()
