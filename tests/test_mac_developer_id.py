import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import installer_builder
from installer_builder import InstallerBuilder

IDENTITY = "Developer ID Application: Example (TEAM123456)"
KEYCHAIN = "/Users/builder/Library/Keychains/codesign.keychain-db"
SIGN = ["codesign", "--force", "--timestamp", "-s", IDENTITY, "--keychain", KEYCHAIN]


@pytest.fixture
def signing(monkeypatch):
    monkeypatch.setenv("MACOS_SIGNING_IDENTITY", IDENTITY)
    monkeypatch.setenv("MACOS_SIGNING_KEYCHAIN", KEYCHAIN)
    monkeypatch.delenv("MACOS_NOTARY_PROFILE", raising=False)
    calls = Mock()
    monkeypatch.setattr(subprocess, "check_call", calls)
    return calls


def test_bundle_is_signed_inside_out_with_hardened_runtime(tmp_path, monkeypatch, signing):
    bundle = tmp_path / "QCast.app"
    version = bundle / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "3.11"
    extension = version / "lib" / "python3.11" / "lib-dynload" / "_ssl.so"
    extension.parent.mkdir(parents=True)
    extension.touch()
    (version / "Python").touch()
    (version / "Resources").mkdir()
    (version / "Resources" / "Info.plist").touch()
    executable = bundle / "Contents" / "MacOS" / "QCast"
    executable.parent.mkdir(parents=True)
    executable.touch()
    machos = {str(extension), str(version / "Python"), str(executable)}
    monkeypatch.setitem(sys.modules, "macholib.util", SimpleNamespace(is_platform_file=lambda path: path in machos))

    installer_builder.codesign_developer_id(str(bundle), IDENTITY)

    targets = [call.args[0][-1] for call in signing.call_args_list]
    assert set(targets) == machos | {str(version), str(bundle)}
    assert targets.index(str(extension)) < targets.index(str(version))
    assert targets.index(str(version / "Python")) < targets.index(str(version))
    assert targets[-1] == str(bundle)
    for call in signing.call_args_list:
        assert call.args[0][:-1] == SIGN + ["--options", "runtime"]


def test_developer_id_signing_replaces_adhoc_even_without_repairs(tmp_path, monkeypatch, signing):
    builder = InstallerBuilder(name="QCast", main_module="main.pyw")
    builder.dist_dir = str(tmp_path)
    bundle = os.path.join(str(tmp_path), "QCast.app")
    monkeypatch.setitem(sys.modules, "installer_builder.mac_bytecode", SimpleNamespace(compile_bundle_sources=lambda *args: False))
    signer = Mock()
    monkeypatch.setattr(installer_builder, "codesign_developer_id", signer)
    adhoc = Mock()
    monkeypatch.setitem(sys.modules, "py2app.util", SimpleNamespace(codesign_adhoc=adhoc))

    builder.repair_mac_dylib_dependencies()

    signer.assert_called_once_with(bundle, IDENTITY)
    adhoc.assert_not_called()
    signing.assert_called_once_with(["codesign", "--verify", "--deep", "--strict", bundle])


def test_signed_image_is_notarized_and_stapled(monkeypatch, signing):
    monkeypatch.setenv("MACOS_NOTARY_PROFILE", "accessibleapps-notary")
    run = Mock(return_value=SimpleNamespace(stdout='{"id": "abc", "status": "Accepted"}'))
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(installer_builder.platform, "system", lambda: "Darwin")
    builder = InstallerBuilder(name="QCast", version="2.0", main_module="main.pyw")
    builder.dist_dir = "dist"
    bundle = os.path.join("dist", "QCast.app")
    image = os.path.join("dist", "QCast-2.0.dmg")

    builder.create_dmg()

    credentials = ["--keychain-profile", "accessibleapps-notary", "--keychain", KEYCHAIN]
    assert run.call_args.args[0] == [
        "xcrun", "notarytool", "submit", image, "--wait", "--output-format", "json",
    ] + credentials
    assert [call.args[0] for call in signing.call_args_list] == [
        ["hdiutil", "create", "-srcfolder", bundle, image],
        SIGN + [image],
        ["xcrun", "stapler", "staple", image],
        ["xcrun", "stapler", "staple", bundle],
    ]


def test_rejected_notarization_prints_log_and_stops_build(monkeypatch, signing):
    monkeypatch.setenv("MACOS_NOTARY_PROFILE", "accessibleapps-notary")
    monkeypatch.setattr(subprocess, "run", Mock(return_value=SimpleNamespace(stdout='{"id": "abc", "status": "Invalid"}')))
    log = Mock()
    monkeypatch.setattr(subprocess, "call", log)
    builder = InstallerBuilder(name="QCast", version="2.0", main_module="main.pyw")

    with pytest.raises(RuntimeError, match="Invalid"):
        builder.create_dmg()

    assert log.call_args.args[0][:4] == ["xcrun", "notarytool", "log", "abc"]
    assert not any("stapler" in call.args[0] for call in signing.call_args_list)
