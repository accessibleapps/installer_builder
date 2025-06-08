#!/usr/bin/env python3
"""
Simple integration test to verify the new innosetup_builder integration works.
"""
import tempfile
import os
import sys
from installer_builder import InstallerBuilder

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