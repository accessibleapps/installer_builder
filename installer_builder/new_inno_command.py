import distutils.core
import os
import pathlib
import platform

# Only import Windows-specific modules on Windows
if platform.system() == "Windows":
    from . import signtool
else:
    signtool = None


def create_installer_config(builder_instance, dist_dir):
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
    installer.main_executable = main_executable_path
    installer.app_short_description = builder_instance.distribution.metadata.description or ""
    installer.run_at_startup = builder_instance.register_startup
    
    # Set output filename
    installer_filename = "-".join([
        installer.app_name, 
        installer.app_version, 
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
        import innosetup_builder
        
        # Create installer config from distribution metadata
        installer_config = create_installer_config(self, self.dist_dir)
        
        # Create compiler and build installer
        innosetup_compiler = innosetup_builder.InnosetupCompiler()
        innosetup_compiler.build(installer_config, self.dist_dir)
        
        output_name = f"{installer_config.app_name}-{installer_config.app_version}-setup.exe"
        print(f"Created installer: {output_name}")
    
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
            
        if signtool is None:
            print(f"Warning: Signing not available on {platform.system()}")
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