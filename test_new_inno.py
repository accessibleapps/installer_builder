#!/usr/bin/env python3
"""
Pytest tests for the new innosetup_builder integration.
"""
import os
import pytest
import re
import sys
import platform
from unittest.mock import call, Mock, patch

from setuptools import Distribution

from installer_builder import InstallerBuilder
from installer_builder import new_inno_command
from installer_builder.signtool import SignToolNotFoundError


REQUESTED_SIGNING_TARGETS = [
    os.path.join("dist", "TestApp.exe"),
    os.path.join("dist", "bootstrap.exe"),
    os.path.join("dist", "TestApp-1.0.0-setup.exe"),
]


class TestInnoSetupIntegration:
    """Test suite for the new innosetup_builder integration."""
    
    def test_installer_builder_basic(self):
        """Test basic InstallerBuilder functionality."""
        builder = InstallerBuilder(
            main_module="test.py",
            name="TestApp",
            version="1.0.0",
            author="Test Author"
        )
        
        assert builder.name == "TestApp"
        assert builder.version == "1.0.0"
        assert builder.author == "Test Author"
        assert builder.main_module == "test.py"
    
    def test_command_class_selection(self):
        """Test that the correct command class is selected based on platform."""
        builder = InstallerBuilder(
            main_module="test.py",
            name="TestApp",
            version="1.0.0"
        )
        
        command_class = builder.get_command_class()
        
        if platform.system() == "Windows":
            assert command_class.__name__ == "NewInnoSetupCommand"
        elif platform.system() == "Darwin":
            # py2app command class
            assert "py2app" in command_class.__name__.lower()
    
    def test_new_inno_command_import(self):
        """Test that NewInnoSetupCommand can be imported."""
        from installer_builder.new_inno_command import NewInnoSetupCommand, create_installer_config
        
        assert NewInnoSetupCommand is not None
        assert create_installer_config is not None
        assert hasattr(NewInnoSetupCommand, 'run')
        assert hasattr(NewInnoSetupCommand, 'description')
    
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-only test")
    def test_new_inno_command_options(self):
        """Test NewInnoSetupCommand options on Windows."""
        from installer_builder.new_inno_command import NewInnoSetupCommand

        cmd = NewInnoSetupCommand(Distribution())
        cmd.initialize_options()
        
        # Test default values
        assert cmd.extra_inno_script is None
        assert cmd.certificate_file is None
        assert cmd.register_startup is False
        assert cmd.dist_dir is None
        assert isinstance(cmd.extra_sign, list)

    def test_create_installer_config_uses_distribution_metadata(self, tmp_path):
        """Build installer metadata from the command's Distribution."""
        from installer_builder.new_inno_command import create_installer_config

        assert callable(create_installer_config)

        distribution = Distribution(
            {
                "name": "TestApp",
                "version": "1.0.0",
                "author": "Test Author",
                "description": "Test Description",
            }
        )
        builder_mock = Mock()
        builder_mock.distribution = distribution
        builder_mock.register_startup = False

        installer = create_installer_config(builder_mock, str(tmp_path))

        assert installer.app_name == "TestApp"
        assert installer.app_version == "1.0.0"
        assert installer.author == "Test Author"
        assert installer.app_short_description == "Test Description"
        assert installer.main_executable == "TestApp.exe"
        assert installer.output_base_filename == "TestApp-1.0.0-setup"


def test_requested_signing_routes_executable_and_bootstrapper():
    distribution = Distribution({"name": "TestApp", "version": "1.0.0"})
    command = new_inno_command.NewInnoSetupCommand(distribution)
    command.dist_dir = "dist"
    command.certificate_file = "certificate.pfx"
    command.certificate_password = "password"
    command.extra_sign = ["bootstrap.exe"]

    with patch.object(
            new_inno_command.os,
            "walk",
            return_value=[("dist", [], ["TestApp.exe", "readme.txt"])],
        ), \
        patch.object(command, "_sign_file") as sign_file:
        command._sign_executables()

    assert sign_file.call_args_list == [
        call(os.path.join("dist", "TestApp.exe")),
        call(os.path.join("dist", "bootstrap.exe")),
    ]


def test_requested_signing_routes_expected_installer():
    distribution = Distribution({"name": "TestApp", "version": "1.0.0"})
    command = new_inno_command.NewInnoSetupCommand(distribution)
    command.dist_dir = "dist"

    with patch.object(command, "_sign_file") as sign_file:
        command._sign_installer()

    sign_file.assert_called_once_with(
        os.path.join("dist", "TestApp-1.0.0-setup.exe")
    )


@pytest.mark.parametrize("target", REQUESTED_SIGNING_TARGETS)
def test_requested_signing_succeeds_for_each_target(target):
    distribution = Distribution(
        {
            "name": "TestApp",
            "version": "1.0.0",
            "url": "https://example.com/TestApp",
        }
    )
    command = new_inno_command.NewInnoSetupCommand(distribution)
    command.certificate_file = "certificate.pfx"
    command.certificate_password = "password"

    with patch.object(new_inno_command.os.path, "exists", return_value=True), \
        patch.object(new_inno_command.signtool, "sign") as sign:
        command._sign_file(target)

    sign.assert_called_once_with(
        target,
        url="https://example.com/TestApp",
        certificate_file="certificate.pfx",
        certificate_password="password",
    )


@pytest.mark.parametrize("target", REQUESTED_SIGNING_TARGETS)
def test_requested_signing_missing_target_fails_for_each_target(target):
    command = new_inno_command.NewInnoSetupCommand(Distribution())
    expected_message = f"File to sign not found: {target}"

    with patch.object(new_inno_command.os.path, "exists", return_value=False), \
        patch.object(new_inno_command.signtool, "sign") as sign, \
        pytest.raises(FileNotFoundError, match=re.escape(expected_message)):
        command._sign_file(target)

    sign.assert_not_called()


@pytest.mark.parametrize("target", REQUESTED_SIGNING_TARGETS)
def test_requested_signing_unavailable_support_fails_for_each_target(target):
    command = new_inno_command.NewInnoSetupCommand(Distribution())
    expected_message = "Signing not available on TestOS"

    with patch.object(new_inno_command.os.path, "exists", return_value=True), \
        patch.object(new_inno_command, "signtool", None), \
        patch.object(new_inno_command.platform, "system", return_value="TestOS"), \
        pytest.raises(RuntimeError, match=re.escape(expected_message)):
        command._sign_file(target)


@pytest.mark.parametrize("target", REQUESTED_SIGNING_TARGETS)
def test_requested_signing_missing_certificate_fails_for_each_target(target):
    command = new_inno_command.NewInnoSetupCommand(Distribution())
    expected_message = "Certificate file not found: missing.pfx"
    error = FileNotFoundError(expected_message)

    with patch.object(new_inno_command.os.path, "exists", return_value=True), \
        patch.object(new_inno_command.signtool, "sign", side_effect=error), \
        pytest.raises(
            FileNotFoundError,
            match=re.escape(expected_message),
        ) as exc_info:
        command._sign_file(target)

    assert exc_info.value is error


@pytest.mark.parametrize("target", REQUESTED_SIGNING_TARGETS)
def test_requested_signing_missing_tool_fails_for_each_target(target):
    command = new_inno_command.NewInnoSetupCommand(Distribution())
    error = SignToolNotFoundError()
    expected_message = str(error)

    with patch.object(new_inno_command.os.path, "exists", return_value=True), \
        patch.object(new_inno_command.signtool, "sign", side_effect=error), \
        pytest.raises(
            SignToolNotFoundError,
            match=re.escape(expected_message),
        ) as exc_info:
        command._sign_file(target)

    assert exc_info.value is error


@pytest.mark.parametrize("target", REQUESTED_SIGNING_TARGETS)
def test_requested_signing_signer_exception_fails_for_each_target(target):
    command = new_inno_command.NewInnoSetupCommand(Distribution())
    error = OSError("sentinel signer failure")

    with patch.object(new_inno_command.os.path, "exists", return_value=True), \
        patch.object(new_inno_command.signtool, "sign", side_effect=error), \
        pytest.raises(OSError) as exc_info:
        command._sign_file(target)

    assert exc_info.value is error


def test_run_stops_before_installer_when_executable_or_bootstrapper_signing_fails():
    command = new_inno_command.NewInnoSetupCommand(Distribution())
    command.certificate_file = "certificate.pfx"
    error = OSError("executable signing failed")
    events = Mock()
    events.sign_executables.side_effect = error

    with patch.object(command, "_sign_executables", events.sign_executables), \
        patch.object(command, "_create_installer", events.create_installer), \
        patch.object(command, "_sign_installer", events.sign_installer), \
        pytest.raises(OSError) as exc_info:
        command.run()

    assert exc_info.value is error
    assert events.mock_calls == [
        call.sign_executables(),
    ]


def test_run_propagates_installer_signing_failure():
    command = new_inno_command.NewInnoSetupCommand(Distribution())
    command.certificate_file = "certificate.pfx"
    error = OSError("installer signing failed")
    events = Mock()
    events.sign_installer.side_effect = error

    with patch.object(command, "_sign_executables", events.sign_executables), \
        patch.object(command, "_create_installer", events.create_installer), \
        patch.object(command, "_sign_installer", events.sign_installer), \
        pytest.raises(OSError) as exc_info:
        command.run()

    assert exc_info.value is error
    assert events.mock_calls == [
        call.sign_executables(),
        call.create_installer(),
        call.sign_installer(),
    ]


def test_legacy_code_still_exists():
    """Test that legacy innosetup.py still exists (until we delete it)."""
    import os
    legacy_path = os.path.join(
        os.path.dirname(__file__), 
        "installer_builder", 
        "innosetup.py"
    )
    assert os.path.exists(legacy_path), "Legacy innosetup.py should still exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
