import sys
from unittest.mock import Mock

import installer_builder
from installer_builder import InstallerBuilder


def test_mac_release_receives_py2app_configuration(monkeypatch):
    monkeypatch.setattr(installer_builder, "is_mac", True)
    monkeypatch.setattr(installer_builder, "is_windows", False)
    monkeypatch.setattr(sys, "argv", ["setup.py", "release"])
    builder = InstallerBuilder(name="QCast", main_module="main.pyw", includes=["platform_utils.blackhole"])
    monkeypatch.setattr(builder, "find_datafiles", lambda: [])
    monkeypatch.setattr(builder, "get_command_class", lambda: None)
    monkeypatch.setattr(builder, "repair_mac_dylib_dependencies", lambda: None)
    setup = Mock()
    monkeypatch.setattr(installer_builder.setuptools, "setup", setup)
    builder.build_installer()
    options = setup.call_args.kwargs["options"]
    assert options["release"] is options["py2app"]
    assert "platform_utils.blackhole" in options["release"]["includes"]


def test_mac_release_creates_image_before_installer_finalization(monkeypatch):
    monkeypatch.setattr(installer_builder, "is_mac", True)
    monkeypatch.setattr(sys, "argv", ["setup.py", "release"])
    builder = InstallerBuilder(name="QCast", main_module="main.pyw")
    events = []
    for method in ("prebuild_message", "remove_previous_build", "build_installer", "create_dmg", "finalize_build", "perform_postbuild_commands", "report_build_statistics"):
        monkeypatch.setattr(builder, method, lambda name=method: events.append(name))
    monkeypatch.setattr(builder, "_installer_was_created", lambda: "create_dmg" in events)
    builder.build()
    assert events.index("create_dmg") < events.index("finalize_build")


def test_mac_image_uses_builder_paths_and_automatic_size(monkeypatch):
    call = Mock()
    monkeypatch.setattr(installer_builder.subprocess, "check_call", call)
    monkeypatch.setattr(installer_builder.platform, "system", lambda: "Darwin")
    builder = InstallerBuilder(name="Test App", version="2.0", main_module="main.pyw")
    builder.dist_dir = "output"
    builder.create_dmg()
    import os
    call.assert_called_once_with([
        "hdiutil", "create", "-srcfolder", os.path.join("output", "Test App.app"),
        os.path.join("output", "Test App-2.0.dmg"),
    ])


def test_mac_update_archive_preserves_bundle_links(monkeypatch):
    import os

    call = Mock()
    monkeypatch.setattr(installer_builder.subprocess, "check_call", call)
    monkeypatch.setattr(installer_builder.platform, "system", lambda: "Darwin")
    builder = InstallerBuilder(name="QCast", version="2.0", main_module="main.pyw")
    builder.create_update_archive()
    call.assert_called_once_with([
        "/usr/bin/ditto", "-c", "-k", "--sequesterRsrc",
        os.path.join(builder.dist_dir, "QCast.app"),
        os.path.join(builder.output_directory, "QCast-2.0-Darwin.zip"),
    ])
