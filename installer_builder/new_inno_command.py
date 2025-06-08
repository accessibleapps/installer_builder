import distutils.core
import os
from . import signtool


def create_installer_config(builder_instance, dist_dir):
    """Convert InstallerBuilder config to innosetup_builder.Installer"""
    from innosetup_builder import Installer, FileEntry, RegistryEntry, all_files
    
    # Get main executable name
    main_exe = f"{builder_instance.name}.exe"
    
    # Scan py2exe output directory  
    files = list(all_files(dist_dir))
    
    # Create installer config
    installer = Installer(
        app_name=builder_instance.name,
        app_version=builder_instance.version,
        author=builder_instance.author or "",
        main_executable=main_exe,
        files=files,
        run_at_startup=builder_instance.register_startup,
        extra_iss=builder_instance.extra_inno_script or ""
    )
    
    # Add startup registry entry if needed
    if builder_instance.register_startup:
        installer.registry_entries.append(
            RegistryEntry(
                root="HKCU", 
                subkey="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                value_type="string",
                value_name=builder_instance.name,
                value_data=f"{{app}}\\{main_exe}",
                flags="uninsdeletevalue"
            )
        )
    
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
    
    def initialize_options(self):
        self.extra_inno_script = None
        self.certificate_file = None
        self.certificate_password = None
        self.extra_sign = []
        self.register_startup = False
        self.dist_dir = None
        
    def finalize_options(self):
        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))
        if self.dist_dir is None:
            self.dist_dir = "dist"
            
    def run(self):
        # Run py2exe first to create executable
        self.run_command('py2exe')
        
        # Sign executables if requested
        if self.certificate_file:
            self._sign_executables()
            
        # Create installer using innosetup_builder
        self._create_installer()
        
        # Sign the installer if requested  
        if self.certificate_file:
            self._sign_installer()
    
    def _create_installer(self):
        from innosetup_builder import InnosetupCompiler
        
        # Create installer config from distribution metadata
        installer_config = create_installer_config(self, self.dist_dir)
        
        # Build the installer
        compiler = InnosetupCompiler()
        output_name = f"{installer_config.app_name}-{installer_config.app_version}-setup.exe"
        output_path = os.path.join(self.dist_dir, output_name)
        
        compiler.build(installer_config, output_path)
        print(f"Created installer: {output_path}")
    
    def _sign_executables(self):
        """Sign all executables in dist directory"""
        for root, _, files in os.walk(self.dist_dir):
            for file in files:
                if file.lower().endswith('.exe'):
                    self._sign_file(os.path.join(root, file))
                    
        # Sign extra files if specified
        if self.extra_sign:
            for extra in self.extra_sign:
                self._sign_file(os.path.join(self.dist_dir, extra))
    
    def _sign_installer(self):
        """Sign the created installer"""
        installer_name = f"{self.distribution.metadata.name}-{self.distribution.metadata.version}-setup.exe"
        installer_path = os.path.join(self.dist_dir, installer_name)
        if os.path.exists(installer_path):
            self._sign_file(installer_path)
    
    def _sign_file(self, filepath):
        """Sign a single file"""
        if not os.path.exists(filepath):
            return
            
        try:
            signtool.sign(
                filepath,
                url=self.distribution.get_url(),
                certificate_file=self.certificate_file,
                certificate_password=self.certificate_password,
            )
            print(f"Signed: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Warning: Failed to sign {filepath}: {e}")