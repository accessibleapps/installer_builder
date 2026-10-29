import sys
from unittest.mock import Mock

import installer_builder
from installer_builder import InstallerBuilder


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
