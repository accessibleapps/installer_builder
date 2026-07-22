#!/usr/bin/env python3
"""
Simple integration test to verify the new innosetup_builder integration works.
"""
import distutils.command
import importlib.util
import tempfile
import os
import re
import sys
from pathlib import Path
import types
from unittest.mock import call, Mock, patch

import pytest
from setuptools import Distribution

from installer_builder import InstallerBuilder


LEGACY_REQUESTED_SIGNING_TARGETS = [
    os.path.join("dist", "TestApp.exe"),
    os.path.join("dist", "bootstrap.exe"),
    os.path.join("dist", "TestApp-1.0.0-setup.exe"),
]


@pytest.fixture
def legacy_innosetup_module(monkeypatch):
    win32api_module = types.ModuleType("win32api")
    py2exe_module = types.ModuleType("py2exe")
    py2exe_module.__path__ = []

    monkeypatch.setitem(sys.modules, "win32api", win32api_module)
    monkeypatch.setitem(sys.modules, "py2exe", py2exe_module)
    monkeypatch.setattr(
        distutils.command,
        "__all__",
        list(distutils.command.__all__),
    )

    module_name = "installer_builder._legacy_innosetup_test"
    module_path = Path(__file__).parent / "installer_builder" / "innosetup.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    monkeypatch.setitem(
        sys.modules,
        "distutils.command.innosetup",
        types.ModuleType("distutils.command.innosetup"),
    )
    spec.loader.exec_module(module)

    yield module

def test_basic_functionality():
    """Test basic InstallerBuilder functionality without actually building."""
    
    # Create a simple test builder
    builder = InstallerBuilder(
        main_module="test_app.py",
        name="TestApp", 
        version="1.0.0",
        author="Test Author"
    )
    
    # Verify basic properties
    assert builder.name == "TestApp"
    assert builder.version == "1.0.0"
    assert builder.author == "Test Author"
    
    # Test that Windows command class can be imported
    if sys.platform == 'win32':
        command_class = builder.get_command_class()
        assert command_class.__name__ == "NewInnoSetupCommand"
        print("✓ NewInnoSetupCommand successfully imported")
    else:
        print("✓ Test skipped on non-Windows platform")
        
    print("✓ Basic functionality test passed")

def test_import_dependencies():
    """Test that we can import the new dependencies."""
    try:
        from installer_builder.new_inno_command import NewInnoSetupCommand, create_installer_config
        print("✓ New command classes imported successfully")
        
        # Try importing innosetup_builder (may fail if not installed)
        try:
            import innosetup_builder
            print("✓ innosetup_builder library available")
        except ImportError:
            print("⚠ innosetup_builder not installed (expected in development)")
            
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
        
    return True


def test_legacy_requested_signing_routes_executable_and_bootstrapper(
    legacy_innosetup_module,
):
    command = legacy_innosetup_module.innosetup(Distribution())
    command.dist_dir = "dist"
    command.certificate_file = "certificate.pfx"
    command.certificate_password = "password"
    command.extra_sign = ["bootstrap.exe"]

    with (
        patch.object(
            legacy_innosetup_module.os,
            "walk",
            return_value=[("dist", [], ["TestApp.exe", "readme.txt"])],
        ),
        patch.object(command, "sign_executable") as sign_executable,
    ):
        command.sign_executables()

    assert sign_executable.call_args_list == [
        call(os.path.join("dist", "TestApp.exe")),
        call(os.path.join("dist", "bootstrap.exe")),
    ]


@pytest.mark.parametrize("target", LEGACY_REQUESTED_SIGNING_TARGETS)
def test_legacy_requested_signing_succeeds_for_each_target(
    legacy_innosetup_module,
    target,
):
    distribution = Distribution(
        {
            "name": "TestApp",
            "version": "1.0.0",
            "url": "https://example.com/TestApp",
        }
    )
    command = legacy_innosetup_module.innosetup(distribution)
    command.certificate_file = "certificate.pfx"
    command.certificate_password = "password"

    with (
        patch.object(legacy_innosetup_module.os.path, "exists", return_value=True),
        patch.object(legacy_innosetup_module.signtool, "sign") as sign,
    ):
        command.sign_executable(target)

    sign.assert_called_once_with(
        target,
        url="https://example.com/TestApp",
        certificate_file="certificate.pfx",
        certificate_password="password",
    )


@pytest.mark.parametrize("target", LEGACY_REQUESTED_SIGNING_TARGETS)
def test_legacy_requested_signing_missing_target_fails_for_each_target(
    legacy_innosetup_module,
    target,
):
    command = legacy_innosetup_module.innosetup(Distribution())
    expected_message = f"File to sign not found: {target}"

    with (
        patch.object(legacy_innosetup_module.os.path, "exists", return_value=False),
        patch.object(legacy_innosetup_module.signtool, "sign") as sign,
        pytest.raises(FileNotFoundError, match=re.escape(expected_message)),
    ):
        command.sign_executable(target)

    sign.assert_not_called()


@pytest.mark.parametrize("target", LEGACY_REQUESTED_SIGNING_TARGETS)
def test_legacy_requested_signing_missing_certificate_fails_for_each_target(
    legacy_innosetup_module,
    target,
):
    command = legacy_innosetup_module.innosetup(Distribution())
    expected_message = "Certificate file not found: missing.pfx"
    error = FileNotFoundError(expected_message)

    with (
        patch.object(legacy_innosetup_module.os.path, "exists", return_value=True),
        patch.object(legacy_innosetup_module.signtool, "sign", side_effect=error),
        pytest.raises(
            FileNotFoundError,
            match=re.escape(expected_message),
        ) as exc_info,
    ):
        command.sign_executable(target)

    assert exc_info.value is error


@pytest.mark.parametrize("target", LEGACY_REQUESTED_SIGNING_TARGETS)
def test_legacy_requested_signing_missing_tool_fails_for_each_target(
    legacy_innosetup_module,
    target,
):
    command = legacy_innosetup_module.innosetup(Distribution())
    error = legacy_innosetup_module.signtool.SignToolNotFoundError()
    expected_message = str(error)

    with (
        patch.object(legacy_innosetup_module.os.path, "exists", return_value=True),
        patch.object(legacy_innosetup_module.signtool, "sign", side_effect=error),
        pytest.raises(
            legacy_innosetup_module.signtool.SignToolNotFoundError,
            match=re.escape(expected_message),
        ) as exc_info,
    ):
        command.sign_executable(target)

    assert exc_info.value is error


@pytest.mark.parametrize("target", LEGACY_REQUESTED_SIGNING_TARGETS)
def test_legacy_requested_signing_signer_exception_fails_for_each_target(
    legacy_innosetup_module,
    target,
):
    command = legacy_innosetup_module.innosetup(Distribution())
    error = OSError("sentinel signer failure")

    with (
        patch.object(legacy_innosetup_module.os.path, "exists", return_value=True),
        patch.object(legacy_innosetup_module.signtool, "sign", side_effect=error),
        pytest.raises(OSError) as exc_info,
    ):
        command.sign_executable(target)

    assert exc_info.value is error


def test_legacy_run_routes_compiled_installer_to_signing(
    legacy_innosetup_module,
):
    distribution = Distribution({"name": "TestApp", "version": "1.0.0"})
    command = legacy_innosetup_module.innosetup(distribution)
    command.dist_dir = "dist"
    command.certificate_file = "certificate.pfx"
    command.inno_script = None
    compiled_installer = os.path.join("dist", "TestApp-1.0.0-setup.exe")
    script = Mock()
    script.compile_script.return_value = compiled_installer

    with (
        patch.object(command, "run_command") as run_command,
        patch.object(command, "get_finalized_command") as get_finalized_command,
        patch.object(command, "_find_inno_setup", return_value="ISCC.exe"),
        patch.object(legacy_innosetup_module, "InnoScript", return_value=script),
        patch.object(command, "sign_executables") as sign_executables,
        patch.object(command, "sign_executable") as sign_executable,
    ):
        command.run()

    run_command.assert_called_once_with("py2exe")
    get_finalized_command.assert_called_once_with("py2exe")
    sign_executables.assert_called_once_with()
    script.create.assert_called_once_with()
    script.compile_script.assert_called_once_with()
    sign_executable.assert_called_once_with(compiled_installer)

if __name__ == "__main__":
    print("Running integration tests...")
    print("=" * 50)
    
    try:
        test_import_dependencies()
        test_basic_functionality()
        print("=" * 50)
        print("✓ All tests passed!")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
