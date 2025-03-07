# Installer Builder

A Python package that simplifies creating Windows and macOS installers for Python applications.

## Features

- Create Windows installers using InnoSetup
- Create macOS DMG installers
- Automatic code signing support
- Bundle Visual C++ runtime libraries
- Support for COM servers and Windows services
- Automatic startup registration
- Localization support
- Update archive creation

## Requirements

### Windows
- Python 2.5 or later
- py2exe
- pywin32
- InnoSetup

### macOS
- py2app

## Installation

```bash
pip install installer_builder
```

## Basic Usage

```python
from installer_builder import InstallerBuilder

builder = InstallerBuilder(
    main_module="your_app.py",
    name="YourApp",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://yourapp.example.com",
)

builder.build()
```

## Advanced Usage

```python
from installer_builder import InstallerBuilder

builder = InstallerBuilder(
    main_module="your_app.py",
    name="YourApp",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://yourapp.example.com",
    datafiles=[("", ["README.md", "LICENSE"])],
    includes=["module1", "module2"],
    excludes=["module3", "module4"],
    extra_packages=["package1", "package2"],
    create_update=True,
    certificate_file="path/to/certificate.pfx",
    register_startup=True,
    has_translations=True,
)

builder.build()
```

## AppInstallerBuilder

For applications that follow a specific structure, you can use the `AppInstallerBuilder`:

```python
from installer_builder import AppInstallerBuilder

class MyApp:
    name = "MyApp"
    version = "1.0.0"
    author = "Your Name"
    website = "https://myapp.example.com"
    
    # Optional attributes
    register_startup = True
    update_endpoint = "https://myapp.example.com/updates"
    
app = MyApp()

builder = AppInstallerBuilder(
    application=app,
    certificate_file="path/to/certificate.pfx",
    has_translations=True,
)

builder.build()
```

## Code Signing

To sign your Windows executables and installer:

```python
builder = InstallerBuilder(
    # ... other parameters
    certificate_file="path/to/certificate.pfx",
    certificate_password="your_password",  # Optional, will prompt if not provided
    extra_files_to_sign=["additional.exe", "library.dll"],
)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
