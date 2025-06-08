#!/usr/bin/env python3
"""
Pytest tests for the new innosetup_builder integration.
"""
import pytest
import sys
import platform
from unittest.mock import Mock, patch

from installer_builder import InstallerBuilder


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
        
        cmd = NewInnoSetupCommand()
        cmd.initialize_options()
        
        # Test default values
        assert cmd.extra_inno_script is None
        assert cmd.certificate_file is None
        assert cmd.register_startup is False
        assert cmd.dist_dir is None
        assert isinstance(cmd.extra_sign, list)
    
    def test_create_installer_config_function_exists(self):
        """Test that create_installer_config function exists and is callable."""
        from installer_builder.new_inno_command import create_installer_config
        
        assert callable(create_installer_config)
        
        # Test function signature by checking it doesn't crash with mock args
        # (actual functionality requires innosetup_builder which may not be installed)
        builder_mock = Mock()
        builder_mock.name = "TestApp"
        builder_mock.version = "1.0.0"
        builder_mock.author = "Test Author"
        builder_mock.register_startup = False
        builder_mock.extra_inno_script = None
        
        # This will fail if innosetup_builder isn't installed, which is expected
        try:
            create_installer_config(builder_mock, "/test/dist")
        except ImportError:
            # Expected when innosetup_builder is not installed
            pass


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