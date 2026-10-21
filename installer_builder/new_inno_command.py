from __future__ import annotations

import distutils.core
from distutils.dist import Distribution
import os
import pathlib
import platform
from types import ModuleType
from typing import TYPE_CHECKING, List, Optional, Protocol, Union, cast

if TYPE_CHECKING:
    import innosetup_builder

Path = Union[str, "os.PathLike[str]"]


class InstallerCommand(Protocol):
    distribution: Distribution
    register_startup: bool

# Only import Windows-specific modules on Windows
if platform.system() == "Windows":
    from . import signtool as _signtool
    signtool: Optional[ModuleType] = _signtool
else:
    signtool = None


def create_installer_config(builder_instance: InstallerCommand, dist_dir: Path) -> innosetup_builder.Installer:
    """Convert InstallerBuilder config to innosetup_builder.Installer"""
    import innosetup_builder
    
    # Get main executable name and path
    main_exe = f"{builder_instance.distribution.metadata.name}.exe"
    main_executable_path = pathlib.Path(dist_dir) / main_exe
    
    # Create installer config
    installer = innosetup_builder.Installer()
    installer.app_name = builder_instance.distribution.metadata.name
    installer.files = innosetup_builder.all_files(dist_dir)
    installer.app_version = builder_instance.distribution.metadata.version
    installer.author = builder_instance.distribution.metadata.author or ""
    installer.main_executable = main_exe
    installer.app_short_description = builder_instance.distribution.metadata.description or ""
    installer.run_at_startup = builder_instance.register_startup
    
    # Set output filename
    app_name, app_version = installer.app_name, installer.app_version
    # The existing join requires strings; retain its TypeError for invalid metadata.
    if not isinstance(app_name, str):
        raise TypeError(f"sequence item 0: expected str instance, {type(app_name).__name__} found")
    if not isinstance(app_version, str):
        raise TypeError(f"sequence item 1: expected str instance, {type(app_version).__name__} found")
    installer_filename = "-".join([
        app_name,
        app_version,
        'setup'
    ])
    installer.output_base_filename = installer_filename
    
    return installer


class NewInnoSetupCommand(distutils.core.Command):
    """Replacement for innosetup.innosetup command using innosetup_builder"""
    
    description = "create an executable installer using Inno Setup"
    
    user_options = [
        ("extra-inno-script=", None, "additional InnoSetup script content"),
        ("certificate-file=", None, "path to signing certificate"),
        ("certificate-password=", None, "password for signing certificate"),
        ("extra-sign=", None, "extra files to be signed"),
        ("register-startup=", None, "register application to run at startup"),
        ("dist-dir=", "d", "directory to put final built distributions in"),
    ]
    
    def initialize_options(self) -> None:
        self.extra_inno_script: Optional[str] = None
        self.certificate_file: Optional[Path] = None
        self.certificate_password: Optional[str] = None
        self.extra_sign: List[Path] = []
        self.register_startup = False
        self.dist_dir: Optional[Path] = None
        
    def finalize_options(self) -> None:
        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))
        if self.dist_dir is None:
            self.dist_dir = "dist"
            
    def run(self) -> None:
        # Sign executables if requested
        if self.certificate_file:
            self._sign_executables()
            
        # Create installer using innosetup_builder
        self._create_installer()
        
        # Sign the installer if requested  
        if self.certificate_file:
            self._sign_installer()
    
    def _create_installer(self) -> None:
        import innosetup_builder
        
        # Create installer config from distribution metadata
        # distutils finalizes options before run(); finalize_options supplies dist.
        dist_dir = cast(Path, self.dist_dir)
        installer_config = create_installer_config(self, dist_dir)
        
        # Create compiler and build installer
        innosetup_compiler = innosetup_builder.InnosetupCompiler()
        innosetup_compiler.build(installer_config, dist_dir)
        
        output_name = f"{installer_config.app_name}-{installer_config.app_version}-setup.exe"
        print(f"Created installer: {output_name}")
    
    def _sign_executables(self) -> None:
        """Sign all executables in dist directory"""
        dist_dir = cast(Path, self.dist_dir)  # finalized before run()
        for root, _, files in os.walk(dist_dir):
            for file in files:
                if file.lower().endswith('.exe'):
                    self._sign_file(os.path.join(root, file))
                    
        # Sign extra files if specified
        if self.extra_sign:
            for extra in self.extra_sign:
                self._sign_file(os.path.join(dist_dir, extra))
    
    def _sign_installer(self) -> None:
        """Sign the created installer"""
        installer_name = f"{self.distribution.metadata.name}-{self.distribution.metadata.version}-setup.exe"
        installer_path = os.path.join(cast(Path, self.dist_dir), installer_name)
        self._sign_file(installer_path)
    
    def _sign_file(self, filepath: Path) -> None:
        """Sign a single file"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File to sign not found: {filepath}")

        if signtool is None:
            raise RuntimeError(f"Signing not available on {platform.system()}")

        signtool.sign(
            filepath,
            url=self.distribution.get_url(),
            certificate_file=self.certificate_file,
            certificate_password=self.certificate_password,
        )
        print(f"Signed: {os.path.basename(filepath)}")
