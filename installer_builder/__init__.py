# * Encoding: UTF-8

from __future__ import annotations, print_function

import setuptools

import builtins as __builtin__
import collections
import datetime
import fnmatch
import getpass
import glob
import importlib
import os
import platform
import shutil
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Dict, Iterator, List, Mapping, Optional, Protocol, Set, Tuple, Type, Union, cast

if TYPE_CHECKING:
    from distutils.core import Command

DataFiles = List[Tuple[str, List[str]]]
Path = Union[str, "os.PathLike[str]"]


class Application(Protocol):
    @property
    def name(self) -> str: ...

is_windows = platform.system() == "Windows"
is_mac = platform.system() == "Darwin"

if "_" not in __builtin__.__dict__:
    __builtin__.__dict__["_"] = lambda x: x
    __builtin__.__dict__["__"] = lambda x: x
    __builtin__.__dict__["lngettext"] = lambda *a: [i for i in a]

__version__ = "1.6.0"


class InstallerBuilder(object):
    build_dirs = ["build", "dist"]
    dist_dir = "dist"
    locale_dir = "locale"
    default_dll_excludes = ["mpr.dll", "powrprof.dll", "mswsock.dll"]
    default_excludes = [
        "email.test",
        "pywin.dialogs",
        "win32pipe",
        "win32wnet",
        "win32com.gen_py",
    ]
    update_archive_format = "zip"
    build_command = "release"

    def __init__(
        self,
        main_module: Optional[Path] = None,
        name: Optional[str] = None,
        version: Optional[str] = None,
        url: Optional[str] = None,
        author: Optional[str] = None,
        author_email: Optional[str] = None,
        datafiles: Optional[DataFiles] = None,
        includes: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
        dll_excludes: Optional[List[str]] = None,
        compressed: bool = False,
        skip_archive: bool = False,
        bundle_level: int = 3,
        optimization_level: int = 1,
        extra_packages: Optional[List[str]] = None,
        datafile_packages: Optional[List[str]] = None,
        output_directory: Path = "release",
        create_update: bool = False,
        postbuild_commands: Optional[Mapping[str, List[str]]] = None,
        osx_frameworks: Optional[List[str]] = None,
        extra_inno_script: Optional[str] = None,
        register_startup: bool = False,
        localized_packages: Optional[List[str]] = None,
        has_translations: bool = False,
        certificate_file: Optional[Path] = None,
        certificate_password: Optional[str] = None,
        extra_files_to_sign: Optional[List[Path]] = None,
        app_type: str = "windows",
    ) -> None:
        super(InstallerBuilder, self).__init__()
        self.main_module = main_module
        self.name = name
        self.version = version
        self.url = url
        self.author = author
        self.author_email = author_email
        if datafiles is None:
            datafiles = []
        self.datafiles = datafiles
        if includes is None:
            includes = []
        self.includes = includes
        if excludes is None:
            excludes = []
        excludes.extend(self.default_excludes)
        excludes.extend(self.get_version_specific_excludes())
        self.excludes = excludes
        if dll_excludes is None:
            dll_excludes = []
        dll_excludes.extend(self.default_dll_excludes)
        self.dll_excludes = dll_excludes
        self.compressed = compressed
        self.skip_archive = skip_archive
        self.bundle_level = bundle_level
        self.optimization_level = optimization_level
        if extra_packages is None:
            extra_packages = []
        self.extra_packages = extra_packages
        if datafile_packages is None:
            datafile_packages = []
        self.datafile_packages = datafile_packages
        self.output_directory = output_directory
        self.create_update = create_update
        if postbuild_commands is None:
            postbuild_commands = {}
        self.postbuild_commands: DefaultDict[str, List[str]] = collections.defaultdict(list)
        self.postbuild_commands.update(postbuild_commands)
        if osx_frameworks is None:
            osx_frameworks = []
        self.osx_frameworks = osx_frameworks
        self.extra_inno_script = extra_inno_script
        self.build_start_time: Optional[float] = None
        self.register_startup = register_startup
        if localized_packages is None:
            localized_packages = []
        self.localized_packages = localized_packages
        self.has_translations = has_translations
        self.certificate_file = certificate_file
        self.certificate_password = certificate_password
        if extra_files_to_sign is None:
            extra_files_to_sign = []
        self.extra_files_to_sign = extra_files_to_sign
        if app_type not in ("windows", "console"):
            raise ValueError("Invalid app type")
        self.app_type = app_type

    def get_version_specific_excludes(self) -> List[str]:
        result = []
        version = float("%d.%d" % (sys.version_info.major, sys.version_info.minor))
        if version < 3.5:
            result.append("jinja2.asyncsupport")
        return result

    def build(self, skip_finalize: bool = False) -> None:
        self.build_start_time = time.time()
        self.prebuild_message()
        self.remove_previous_build()
        self.build_installer()

        # Check if installer was actually created after running build_installer
        if not skip_finalize and self._installer_was_created():
            self.finalize_build()
            self.perform_postbuild_commands()
            self.report_build_statistics()
        else:
            print(
                "Skipping finalization - no installer was created (py2exe/py2app only)"
            )
            self.report_build_time()

    def _installer_was_created(self) -> bool:
        """Check if an installer file was actually created by the build process"""
        try:
            installer_path = self.find_created_installer()
            return os.path.exists(installer_path)
        except RuntimeError:
            # If installer doesn't exist, no installer was created
            return False

    def prebuild_message(self) -> None:
        print("Installer builder version %s" % __version__)
        print(
            "Building %s installer for %s %s"
            % (platform.system(), self.name, self.version)
        )

    def remove_previous_build(self) -> None:
        print("Removing previous output directories")
        directories = self.build_dirs + [self.output_directory]
        for directory in directories:
            if not os.path.exists(directory):
                continue
            print("Deleting %s" % directory)
            shutil.rmtree(directory, ignore_errors=False)
            print("Deleted ", directory)

    def find_datafiles(self) -> DataFiles:
        datafiles: DataFiles = []
        for package in self.datafile_packages:
            pkg_datafile_function = DATAFILE_REGISTRY.get(package)
            if pkg_datafile_function is None:
                pkg = importlib.import_module(package)
                pkg_datafile_function = pkg.find_datafiles
            pkg_datafiles = pkg_datafile_function()
            datafiles.extend(pkg_datafiles)
            print("Added %d datafiles from package %s" % (len(pkg_datafiles), package))

        if self.has_translations:
            app_lang_data = list(self.find_application_language_data())
            datafiles.extend(app_lang_data)
            print("Added %d application language datafiles" % len(app_lang_data))

            babel_data = list(self.find_babel_datafiles())
            datafiles.extend(babel_data)
            print("Added %d babel datafiles" % len(babel_data))

        for package in self.localized_packages:
            pkg = importlib.import_module(package)
            path = pkg.__path__[0]
            locale_path = os.path.join(path, self.locale_dir)
            domains = self._validate_translation_inventory(locale_path)
            files = list(self.find_locale_data(locale_path))
            datafiles.extend(files)
            print(
                "Added %d locale datafiles for %s; translation domains: %s"
                % (len(files), package, ", ".join(domains))
            )

        total_datafiles = len(self.datafiles) + len(datafiles)
        print("Total datafiles to be included: %d" % total_datafiles)
        return self.datafiles + datafiles

    def find_application_language_data(self) -> Iterator[Tuple[str, List[str]]]:
        self._validate_translation_inventory(
            self.locale_dir, expected_domain=self.name
        )
        for directory, filenames in self.find_locale_data(self.locale_dir):
            yield directory, filenames

    def _validate_translation_inventory(self, locale_path: Path, expected_domain: Optional[str] = None) -> Tuple[str, ...]:
        application_mode = expected_domain is not None
        catalog_extensions = (".po", ".mo") if application_mode else (".mo",)
        catalogs = []

        for dirpath, dirnames, filenames in os.walk(locale_path):
            dirnames.sort()
            for filename in sorted(filenames):
                stem, extension = os.path.splitext(filename)
                extension = extension.lower()
                if extension not in catalog_extensions:
                    continue

                path = os.path.join(dirpath, filename)
                if filename.startswith("._"):
                    raise ValueError(
                        "Invalid translation catalog metadata: %s; "
                        "AppleDouble files are not translation catalogs" % path
                    )

                relative_path = os.path.relpath(path, start=locale_path)
                path_parts = relative_path.split(os.sep)
                valid_layout = (
                    len(path_parts) == 3
                    and path_parts[0] not in ("", ".")
                    and path_parts[1] in ("LC_MESSAGES", "lc_messages")
                )
                if not valid_layout:
                    if application_mode:
                        expected_layout = (
                            "<locale>/(LC_MESSAGES|lc_messages)/<domain>.po or .mo"
                        )
                    else:
                        expected_layout = (
                            "<locale>/(LC_MESSAGES|lc_messages)/<domain>.mo"
                        )
                    raise ValueError(
                        "Invalid translation catalog layout: %s; expected %s"
                        % (path, expected_layout)
                    )

                catalogs.append((path, dirpath, stem, extension))

        if application_mode:
            unexpected_domains = sorted(
                {stem for _, _, stem, _ in catalogs if stem != expected_domain}
            )
            if unexpected_domains:
                found_domain = unexpected_domains[0]
                catalog_directory = min(
                    directory
                    for _, directory, stem, _ in catalogs
                    if stem == found_domain
                )
                raise ValueError(
                    "Translation domain mismatch in %s: expected %r, found %r"
                    % (catalog_directory, expected_domain, found_domain)
                )

            inventory: Dict[Tuple[str, str], Set[str]] = {}
            for _, directory, stem, extension in catalogs:
                inventory.setdefault((directory, stem), set()).add(extension)

            for directory, stem in sorted(inventory):
                if ".po" in inventory[(directory, stem)] and ".mo" not in inventory[
                    (directory, stem)
                ]:
                    expected_mo_path = os.path.join(directory, stem + ".mo")
                    raise FileNotFoundError(
                        "Compiled translation catalog not found: %s"
                        % expected_mo_path
                    )

            for directory, stem in sorted(inventory):
                if ".mo" in inventory[(directory, stem)] and ".po" not in inventory[
                    (directory, stem)
                ]:
                    expected_po_path = os.path.join(directory, stem + ".po")
                    raise FileNotFoundError(
                        "Source translation catalog not found: %s" % expected_po_path
                    )

            if not catalogs:
                raise FileNotFoundError(
                    "No translation catalogs found in: %s" % locale_path
                )
        elif not catalogs:
            raise FileNotFoundError(
                "No compiled translation catalogs found in: %s" % locale_path
            )

        return tuple(sorted({stem for _, _, stem, extension in catalogs if extension == ".mo"}))

    def find_babel_datafiles(self) -> Tuple[Tuple[str, List[str]], ...]:
        babel = importlib.import_module("babel")

        return (
            (
                "locale-data",
                glob.glob(os.path.join(cast(List[str], babel.__path__)[0], "locale-data", "*.*")),
            ),
        )

    def find_locale_data(self, locale_path: Path) -> Iterator[Tuple[str, List[str]]]:
        for dirpath, dirnames, filenames in os.walk(locale_path):
            files = []
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if filename.lower().endswith(".mo"):
                    files.append(path)
            if files:
                directory = os.path.join(
                    self.locale_dir, os.path.relpath(dirpath, start=locale_path)
                )
                yield directory, files

    def finalize_build(self) -> None:
        print("Finalizing build...")
        if platform.system() == "Darwin":
            self.remove_embedded_interpreter()
            self.shrink_mac_binaries()
            self.lipo_file(os.path.join(self.get_app_path(), cast(str, self.name)))
            self.create_dmg()

        # Only move output if installer was created
        try:
            self.move_output()
        except RuntimeError as e:
            print("Warning: Could not move installer output: %s" % e)
            return

        if self.create_update:
            self.create_update_archive()

    def remove_embedded_interpreter(self) -> None:
        print("Replacing the embedded interpreter with a dumby file")
        interpreter_path = os.path.join(self.get_app_path(), "python")
        os.remove(interpreter_path)
        self.execute_command("touch %s" % interpreter_path)
        self.execute_command("chmod +x %s" % interpreter_path)

    def get_app_path(self) -> Path:
        if platform.system() == "Darwin":
            return os.path.join(
                self.dist_dir, "%s.app" % self.name, "Contents", "MacOS"
            )
        return self.dist_dir

    def create_dmg(self) -> None:
        print("Creating .dmg disk image")
        self.execute_command(
            "hdiutil create -srcfolder dist/%s.app -size 150m dist/%s"
            % (self.name, self.installer_filename())
        )

    def move_output(self) -> None:
        if not os.path.exists(self.output_directory):
            os.mkdir(self.output_directory)
        destination = os.path.join(self.output_directory, self.installer_filename())
        os.rename(self.find_created_installer(), destination)
        print("Moved generated installer to %s" % destination)

    def create_update_archive(self) -> None:
        print("Generating update archive")
        name = "%s-%s-%s" % (self.name, self.version, platform.system())
        root_dir = self.dist_dir
        if platform.system() == "Darwin":
            root_dir = os.path.join(root_dir, "%s.app" % self.name)
        filename = shutil.make_archive(
            name, self.update_archive_format, root_dir=root_dir
        )
        filename = os.path.split(filename)[-1]
        destination = os.path.join(self.output_directory, filename)
        os.rename(filename, destination)
        print("Generated update archive filename: %s" % destination)

    def find_created_installer(self) -> str:
        res = os.path.join("dist", self.installer_filename())
        if not os.path.exists(res):
            res = os.path.join(self.output_directory, self.installer_filename())
            if not os.path.exists(res):
                raise RuntimeError("Installer %s does not exist" % res)
        return res

    def installer_filename(self) -> str:
        if platform.system() == "Windows":
            return "%s-%s-setup.exe" % (self.name, self.version)
        elif platform.system() == "Darwin":
            return "%s-%s.dmg" % (self.name, self.version)
        else:
            # Fallback for other systems
            return "%s-%s-installer" % (self.name, self.version)

    def get_command_class(self) -> Optional[Type[Command]]:
        if platform.system() == "Windows":
            from .new_inno_command import NewInnoSetupCommand

            return NewInnoSetupCommand
        elif platform.system() == "Darwin":
            import py2app.build_app

            return py2app.build_app.py2app
        return None

    def perform_postbuild_commands(self) -> None:
        if not self.postbuild_commands[platform.system().lower()]:
            return
        print("Performing postbuild commands for platform %s" % platform.system())
        for command in self.postbuild_commands[platform.system().lower()]:
            self.execute_command(command)

    def execute_command(self, command: str) -> None:
        subprocess.check_call([command], shell=True)

    def report_build_statistics(self) -> None:
        try:
            installer_path = self.find_created_installer()
            print("Generated installer filename: %s" % installer_path)
            print(
                "Generated installer filesize: %s"
                % format_filesize(os.stat(installer_path).st_size)
            )
        except RuntimeError:
            print("Build completed - no installer created (py2exe/py2app only)")
        self.report_build_time()

    def shrink_mac_binaries(self) -> None:
        shrink_extensions = (".dylib", ".so")
        for basepath, dirs, files in os.walk(self.dist_dir):
            for file in files:
                if os.path.splitext(file)[-1] in shrink_extensions:
                    path = os.path.join(basepath, file)
                    self.lipo_file(path)

    def lipo_file(self, filename: Path) -> None:
        self.execute_command("lipo -thin i386 %s -output %s" % (filename, filename))
        print("Lipoed file %s" % filename)

    def report_build_time(self) -> None:
        # build() records this before either path that reports elapsed time.
        build_time = time.time() - cast(float, self.build_start_time)
        td = datetime.timedelta(seconds=build_time)
        print("Build completed in ", format(td))

    def build_installer(self) -> None:
        if None in (self.name, self.main_module):
            raise RuntimeError("Insufficient information provided to build")
        if (
            is_windows
            and self.certificate_file is not None
            and self.certificate_password is None
        ):
            self.certificate_password = os.environ.get(
                "CERTIFICATE_PASS"
            ) or getpass.getpass("Certificate password:")
        # setuptools/py2exe accept heterogeneous, extensible keyword payloads.
        setup_arguments: Dict[str, Any] = {
            "name": self.name,
            "author": self.author,
            "author_email": self.author_email,
            "url": self.url,
            "version": self.version,
            "packages": setuptools.find_packages(),
            "data_files": self.find_datafiles(),
            "options": {
                "py2exe": {
                    "compressed": self.compressed,
                    "bundle_files": self.bundle_level,
                    "includes": self.includes,
                    "excludes": self.excludes,
                    "packages": self.extra_packages,
                    "dll_excludes": self.dll_excludes,
                    "optimize": self.optimization_level,
                    "skip_archive": self.skip_archive,
                },
                "innosetup": {
                    "extra_inno_script": self.extra_inno_script,
                    "register_startup": self.register_startup,
                    "certificate_file": self.certificate_file,
                    "certificate_password": self.certificate_password,
                    "extra_sign": self.extra_files_to_sign,
                },
                "py2app": {
                    "compressed": self.compressed,
                    "includes": self.includes + self.extra_packages,
                    "excludes": self.excludes,
                    "frameworks": self.osx_frameworks,
                    "optimize": self.optimization_level,
                    "argv_emulation": True,
                    "plist": {
                        "CFBundleName": self.name,
                        "CFBundleShortVersionString": self.version,
                        "CFBundleGetInfoString": "%s %s" % (self.name, self.version),
                        "CFBundleExecutable": self.name,
                    },
                },
            },
            self.app_type: [
                {
                    "script": self.main_module,
                    "dest_base": self.name,
                    "company_name": self.author,
                    "copyright": self.get_copyright(),
                }
            ],
            "cmdclass": {
                self.build_command: self.get_command_class(),
                # Also register as innosetup for backward compatibility
                "innosetup": self.get_command_class(),
            },
        }
        if is_mac:
            setup_arguments["app"] = [self.main_module]
        if is_windows:
            from . import innosetup

            setup_arguments[self.app_type][0]["other_resources"] = (
                innosetup.manifest(self.name),
            )
            requested_commands = set(sys.argv[1:])
            if {"py2exe", "innosetup", self.build_command} & requested_commands:
                import py2exe

                targets = setup_arguments[self.app_type]
                py2exe.freeze(
                    console=targets if self.app_type == "console" else [],
                    windows=targets if self.app_type == "windows" else [],
                    data_files=setup_arguments["data_files"],
                    options=setup_arguments["options"]["py2exe"],
                    version_info={
                        "version": self.version,
                        "company_name": self.author,
                        "copyright": self.get_copyright(),
                        "product_name": self.name,
                        "product_version": self.version,
                    },
                )
                if "py2exe" in requested_commands:
                    return
        setuptools.setup(**setup_arguments)
        if is_mac and {"py2app", self.build_command} & set(sys.argv[1:]):
            self.repair_mac_dylib_dependencies()

    def repair_mac_dylib_dependencies(self) -> None:
        """Resolve bundled sibling libraries before re-signing the modified app."""
        bundle = os.path.join(self.dist_dir, "%s.app" % self.name)
        changed = False
        for directory, _, filenames in os.walk(bundle):
            for filename in filenames:
                if not filename.endswith((".dylib", ".so")):
                    continue
                binary = os.path.join(directory, filename)
                dependencies = subprocess.check_output(["otool", "-L", binary], text=True)
                for dependency in sorted({line.strip().split(" (", 1)[0] for line in dependencies.splitlines()}):
                    if not dependency.startswith("@rpath/"):
                        continue
                    sibling = os.path.basename(dependency)
                    if sibling == filename or not os.path.isfile(os.path.join(directory, sibling)):
                        continue
                    subprocess.check_call([
                        "install_name_tool", "-change", dependency,
                        "@loader_path/" + sibling, binary,
                    ])
                    changed = True
        if changed:
            from py2app.util import codesign_adhoc

            codesign_adhoc(bundle)
            subprocess.check_call(["codesign", "--verify", "--deep", "--strict", bundle])

    def get_copyright(self) -> str:
        return "Copyright ©%d %s" % (datetime.date.today().year, self.author)


class AppInstallerBuilder(InstallerBuilder):
    def __init__(self, application: Optional[Application] = None, **kwargs: Any) -> None:
        self.application = application
        # Application providers and forwarded builder keyword options are dynamic.
        new_kwargs: Dict[str, Any] = {}
        new_kwargs["name"] = cast(Application, application).name
        new_kwargs["version"] = getattr(application, "version", None)
        new_kwargs["url"] = getattr(application, "website", None)
        new_kwargs["author"] = getattr(application, "author", None)
        files_to_sign = kwargs.get("extra_files_to_sign", [])
        datafiles = kwargs.get("datafiles", [])
        datafile_packages = kwargs.get("datafile_packages", [])
        includes = kwargs.get("includes", [])
        has_translations = kwargs.get("has_translations", False)
        if has_translations:
            if is_windows:
                import py2exe.hooks

                py2exe.hooks.hook_babel_localedata = lambda finder, module: None
            includes.append("babel.plural")
        extra_packages = kwargs.get("extra_packages", [])
        localized_packages = kwargs.get("localized_packages", [])
        config_spec = getattr(application, "config_spec", None)
        if config_spec is True:
            config_spec = "%s.confspec" % cast(Application, application).name
        if config_spec is not None:
            datafiles.extend([("", [config_spec])])
        babel = importlib.import_module("babel")

        datafiles.extend([("babel", [os.path.join(cast(List[str], babel.__path__)[0], "global.dat")])])
        cert_path = importlib.import_module("certifi").__file__

        datafiles.extend(
            [("", [os.path.join(os.path.dirname(cast(str, cert_path)), "cacert.pem")])]
        )
        kwargs["datafiles"] = datafiles
        if getattr(application, "output", False):
            datafile_packages.append("accessible_output2")
        if getattr(application, "sound", False) or getattr(
            application, "UI_sounds", False
        ):
            datafile_packages.append("sound_lib")
        if getattr(application, "update_endpoint", False):
            datafile_packages.append("autoupdate")
            new_kwargs["create_update"] = True
            files_to_sign.append("bootstrap.exe")
        kwargs["datafile_packages"] = datafile_packages
        activation_module = getattr(application, "activation_module", None)
        if activation_module:
            # Because it's not picked up on OSX.
            extra_packages.append("product_key")
            includes.append(activation_module)
        kwargs["extra_packages"] = extra_packages
        if activation_module:
            localized_packages.append("product_key")
        main_window_class = getattr(application, "main_window_class", None)
        if main_window_class:
            localized_packages.append("wx")
            if importlib.util.find_spec("app_elements") is not None:
                localized_packages.append("app_elements")
            if isinstance(main_window_class, str):
                includes.append(".".join(main_window_class.split(".")[:-1]))
        kwargs["localized_packages"] = localized_packages
        kwargs["includes"] = includes
        kwargs["extra_files_to_sign"] = files_to_sign
        new_kwargs.update(kwargs)
        if hasattr(application, "register_startup"):
            new_kwargs["register_startup"] = getattr(application, "register_startup")
        if hasattr(application, "debug_port") or hasattr(application, "debug_host"):
            if sys.version_info.major < 3:
                includes.append("SocketServer")  # not picked up on Mac
            else:
                includes.append("socketserver")
        new_kwargs["includes"] = includes
        super(AppInstallerBuilder, self).__init__(**new_kwargs)


def format_filesize(num: float) -> Optional[str]:
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return None


def standard_wx_excludes() -> List[str]:
    return [
        "wx.py",
        "wx.stc",
    ]


def sqlite_sqlalchemy_excludes() -> List[str]:
    return [
        "sqlalchemy.testing",
        "sqlalchemy.dialects.postgresql",
        "sqlalchemy.dialects.mysql",
        "sqlalchemy.dialects.oracle",
        "sqlalchemy.dialects.mssql",
        "sqlalchemy.dialects.firebird",
        "sqlalchemy.dialects.sybase",
        "sqlalchemy.dialects.drizzle",
    ]


def app_framework_excludes() -> List[str]:
    return [
        "watchdog",
        "yappi",
        "pytest",
        "pyreadline",
        "nose",
    ]


def stdlib_excludes(pdb: bool = True) -> List[str]:
    res = [
        "doctest",
        "email.test",
        "ftplib",
        "tarfile",
    ]
    if pdb:
        res += [
            "bdb",
            "pdb",
        ]
    return res


def win32_excludes() -> List[str]:
    return [
        "win32pipe",
        "win32wnet",
        "win32evtlog",
    ]


def get_datafiles(directory: Path = "share", match: str = "*", target_path: Optional[str] = None) -> DataFiles:
    """builds list of data files to be included with data_files in setuptools
    A typical task in a setup.py file is to set the path and name of a list
    of data files to provide with the package. For instance files in share/data
    directory. One difficulty is to find those files recursively. This can be
    achieved with os.walk or glob. Here is a simple function that perform this
    task.

    .. todo:: exclude pattern
    """
    print(
        "Searching for datafiles in directory: %s with pattern: %s" % (directory, match)
    )
    ppath = os.path.split(os.path.abspath(sys.executable))[0]
    site_packages = os.path.join(ppath, "lib", "site-packages", "")
    datafiles = []
    matches = []

    for root, dirnames, filenames in os.walk(directory):
        target_path = root.replace(site_packages, "")
        matched_files = fnmatch.filter(filenames, match)
        if matched_files:
            print("  Found %d matching files in %s" % (len(matched_files), root))

        for filename in matched_files:
            matches.append(os.path.join(root, filename))
            this_filename = os.path.join(root, filename)
            datafiles.append((target_path, [this_filename]))

    print(
        "Total files found matching '%s' in %s: %d" % (match, directory, len(datafiles))
    )
    return datafiles


def pytz_datafiles() -> DataFiles:
    pytz = importlib.import_module("pytz")

    path = os.path.join(os.path.split(cast(str, pytz.__file__))[0], "zoneinfo")
    print("Collecting pytz datafiles from: %s" % path)
    files = get_datafiles(path, "*")
    index = path.index("zoneinfo")
    files = [(i[0][index:], i[1]) for i in files]
    print("Found %d pytz zoneinfo files" % len(files))
    return files


def enchant_datafiles() -> DataFiles:
    enchant = importlib.import_module("enchant")

    enchant_path = os.path.split(cast(str, enchant.__file__))[0]
    print("Collecting enchant datafiles from: %s" % enchant_path)

    dll_files = get_datafiles(enchant_path, "*.dll")
    print("Found %d enchant DLL files" % len(dll_files))

    dic_files = get_datafiles(enchant_path, "*.dic", target_path="")
    print("Found %d enchant dictionary files" % len(dic_files))

    aff_files = get_datafiles(enchant_path, "*.aff", target_path="")
    print("Found %d enchant affix files" % len(aff_files))

    files = []
    files.extend(dll_files)
    files.extend(dic_files)
    files.extend(aff_files)

    index = enchant_path.index("enchant") + 8
    files = [(i[0][index:], i[1]) for i in files]
    print("Total enchant datafiles: %d" % len(files))
    return files


DATAFILE_REGISTRY: Dict[str, Callable[[], DataFiles]] = {
    "enchant": enchant_datafiles,
    "pytz": pytz_datafiles,
}
