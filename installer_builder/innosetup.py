"""distutils extension module - create an installer by InnoSetup.

Requirements
------------

* Python 2.5 or later

* `py2exe <http://pypi.python.org/pypi/py2exe>`_

* `pywin32 <http://pypi.python.org/pypi/pywin32>`_

* `InnoSetup <http://www.innosetup.com/>`_


Features
--------

* You can use your customized InnoSetup Script.

* installer metadata over setup() metadata

* generate AppId(GUID) from setup() metadata
  See the innosetup.InnoScript.appid property.

* bundle exe and com dll and dependent libs and resources

* bundle msvcr and mfc and their manifest

* bundle all installed InnoSetup's language file
  (If there is no valid [Languages] section.)

* create `windows` exe's shortcut

* register `com_server` and `service`

* check the Windows version with Python version

* fix a problem py2exe.mf misses some modules (ex. win32com.shell)


An example
----------
::

 from distutils.core import setup
 import py2exe, innosetup
import os
##Have distutils not mess with our versions
import distutils.version
distutils.version.StrictVersion = distutils.version.Version
 # All options are same as py2exe options.
 setup(
  name='example',
  version='1.0.0.0',
  license='PSF or other',
  author='you',
  author_email='you@your.domain',
  description='description',
  url='http://www.your.domain/example', # generate AppId from this url
  options={
   'py2exe': {
    # `innosetup` gets the `py2exe`'s options.
    'compressed': True,
    'optimize': 2,
    'bundle_files': 3,
    },
   'innosetup': {
    # user defined iss file path or iss string
    'inno_script': innosetup.DEFAULT_ISS, # default is ''
    # bundle msvc files
    'bundle_vcr': True, # default is True
    # zip setup file
    'zip': False, # default is False, bool() or zip file name
    # create shortcut to startup if you want.
    'register_startup': True, # default is False
    }
   },
  com_server=[
   {'modules': ['your_com_server_module'], 'create_exe': False},
   ],
  # and other metadata ...
  )

Do the command `setup.py innosetup`.
Then you get InnoSetup script file named `dist\distutils.iss` and
the installation file named `dist\example-1.0.0.0.exe`.


History
-------

0.6.3
-----

* change versioning policy (remove build number).

* add utf-8 bom to .iss file by Jerome Ortais, thanx.

* pick up `COPYING` file for `[setup]/LicenseFile` by Jerome Ortais, thanx.

0.6.0.2
~~~~~~~

* add `regist_startup` option for create shortcut to startup.

0.6.0.1
~~~~~~~

* fix metadata and unicode by surgo, thanx.

* set `DEFAULT_ISS` to empty because `Inno Setup 5.3.9` is released.

* fix a problem that `py2exe` includes MinWin's ApiSet Stub DLLs on Windows 7.

0.6.0.0
~~~~~~~

* support bundling tcl files

* change OutputBaseFilename

0.5.0.1
~~~~~~~

* improve update install support

0.5.0.0
~~~~~~~

* add DEFAULT_ISS, manifest, srcname, srcnames

* add `zip` option

* fix `bundle_files=1` option problem (always bundle pythonXX.dll)

* add `DefaultGroupName`, `InfoBeforeFile`, `LicenseFile` into `[Setup]`
  section

0.4.0.0
~~~~~~~

* support service cmdline_style options

* rewrite codes around iss file

0.3.0.0
~~~~~~~

* improve the InnoSetup instllation path detection

* add `inno_setup_exe` option

0.2.0.0
~~~~~~~

* handle `py2exe`'s command options

* add `bundle_vcr` option

0.1.0.0
~~~~~~~

* first release


"""

from __future__ import absolute_import, print_function
import distutils.command
import distutils.core

import ctypes
import io
import os
import platform
import re
import subprocess
import sys
import uuid
import importlib.machinery
import importlib.util

import winreg
import shutil
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

import win32api  # for read pe32 resource
from py2exe.distutils_buildexe import py2exe

# Modern py2exe uses a different approach
import py2exe


from . import signtool

RT_MANIFEST = 24

DEFAULT_ISS = ""
DEFAULT_CODES = """
procedure ExecIfExists(const FileName, Arg: String);
var
 ret: Integer;
begin
 FileName := ExpandConstant(FileName);
 if FileExists(FileName) then begin
  if not Exec(FileName, Arg, '', SW_HIDE, ewWaitUntilTerminated, ret) then
   RaiseException('error: ' + FileName + ' ' + Arg);
 end;
end;
procedure UnregisterPywin32Service(const FileName: String);
begin
 try
  ExecIfExists(FileName, 'stop');
 except
  //already stopped or stop error
 end;
 ExecIfExists(FileName, 'remove');
end;
procedure UnregisterServerIfExists(const FileName: String);
begin
 FileName := ExpandConstant(FileName);
 if FileExists(FileName) then begin
  if not UnregisterServer(%(x64)s, FileName, False) then
   RaiseException('error: unregister ' + FileName);
 end;
end;
""" % {
    "x64": platform.machine() == "AMD64",
}


# Modern manifest template for Windows applications
MANIFEST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
    <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
        <application>
            <!-- Windows Vista -->
            <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
            <!-- Windows 7 -->
            <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
            <!-- Windows 8 -->
            <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
            <!-- Windows 8.1 -->
            <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
            <!-- Windows 10/11 -->
            <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
        </application>
    </compatibility>
    <assemblyIdentity
     type="win32"
     name="Controls"
     version="5.0.0.0"
     processorArchitecture="*"
    />
    <description>%s</description>
    <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
        <security>
            <requestedPrivileges>
                <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
            </requestedPrivileges>
        </security>
    </trustInfo>
    <dependency>
        <dependentAssembly>
            <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
        </dependentAssembly>
    </dependency>
    <application xmlns="urn:schemas-microsoft-com:asm.v3">
        <windowsSettings>
            <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2019/WindowsSettings">PerMonitorV2, PerMonitor</dpiAwareness>
            <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
        </windowsSettings>
    </application>
</assembly>"""

def manifest(name, res_id=1):
    """Create a manifest resource with the given name."""
    data = MANIFEST_TEMPLATE % name
    return RT_MANIFEST, res_id, data.encode('utf-8')


README_EXT = ".html"


def load_manifest(handle):
    """get the first manifest string from HMODULE"""
    for restype in (RT_MANIFEST,):  # win32api.EnumResourceTypes(handle)
        for name in win32api.EnumResourceNames(handle, restype):
            return win32api.LoadResource(handle, restype, name).decode("utf_8")


def srcname(dottedname):
    """get the source filename from importable name or module"""
    if hasattr(dottedname, "__file__"):
        module = dottedname
    else:
        names = dottedname.split(".")
        module = __import__(names.pop(0))
        for name in names:
            module = getattr(module, name)

    filename = module.__file__
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    # Get source suffixes using importlib
    _py_src_suffixes = [s.suffix for s in importlib.machinery.SOURCE_SUFFIXES]

    if ext in _py_src_suffixes:
        return filename

    for i in _py_src_suffixes:
        if os.path.isfile(name + i):
            return name + i

    raise ValueError(f"Source file not found for {dottedname}")


def srcnames(*args):
    """get the source filename from importable name or module"""
    return [srcname(i) for i in args]


def modname(handle):
    """get module filename from HMODULE"""
    b = ctypes.create_unicode_buffer("", 1024)
    ctypes.windll.kernel32.GetModuleFileNameW(handle, b, 1024)
    return b.value


def findfiles(filenames, *conditions):
    """filter `filenames` by conditions"""

    def check(filename):
        filename = filename.lower()
        for i in conditions:
            i = i.lower()
            if i.startswith("."):  # compare ext
                if os.path.splitext(filename)[1] != i:
                    return
            elif i.count(".") == 1:  # compare basename
                if os.path.basename(filename) != i:
                    return
            else:  # contains
                if i not in os.path.basename(filename):
                    return
        return True

    return [i for i in filenames if check(i)]


hkshortnames = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKCR": winreg.HKEY_CLASSES_ROOT,
    "HKU": winreg.HKEY_USERS,
    "HKCC": winreg.HKEY_CURRENT_CONFIG,
    "HKPD": winreg.HKEY_PERFORMANCE_DATA,
}


def getregvalue(path, default=None):
    """get registry value

    noname value
    >>> getregvalue('HKEY_CLASSES_ROOT\\.py\\')
    'Python.File'

    named value
    >>> getregvalue('HKEY_CLASSES_ROOT\\.py\\Content Type')
    ''text/plain
    """
    root, subkey = path.split("\\", 1)
    if root.startswith("HKEY_"):
        root = getattr(winreg, root)
    elif root in hkshortnames:
        root = hkshortnames[root]
    else:
        root = winreg.HKEY_CURRENT_USER
        subkey = path

    subkey, name = subkey.rsplit("\\", 1)

    try:
        handle = winreg.OpenKey(root, subkey)
        value, typeid = winreg.QueryValueEx(handle, name)
        return value
    except OSError:
        return default


class IssFile(io.TextIOWrapper):
    """file object with useful method `issline`"""

    noescape = [
        "Flags",
    ]

    def __init__(self, filename, mode='w', encoding='utf-8'):
        # Open a buffered binary file and wrap it
        binary_file = open(filename, mode.replace('t', '') + 'b')
        super().__init__(binary_file, encoding=encoding)
        # Write BOM for better compatibility with Inno Setup
        if 'w' in mode and encoding.lower() == 'utf-8':
            self.write('\ufeff')  # UTF-8 BOM

    def issline(self, **kwargs):
        args = []
        for k, v in kwargs.items():
            if k not in self.noescape:
                # ' -> ''
                if isinstance(v, str):
                    v = '"%s"' % v.replace('"', '""')
                else:
                    v = '"%s"' % v
            args.append(f"{k}: {v}")
        self.write("; ".join(args) + "\n")


class InnoScript(object):
    """Class to create and compile an Inno Setup script."""
    
    consts_map = dict(
        AppName="%(name)s",
        AppVerName="%(name)s %(version)s",
        AppVersion="%(version)s",
        VersionInfoVersion="%(version)s",
        AppCopyright="%(author)s",
        AppContact="%(author_email)s",
        AppComments="%(description)s",
        AppPublisher="%(author)s",
        AppPublisherURL="%(url)s",
        AppSupportURL="%(url)s",
    )
    metadata_map = dict(
        SolidCompression="yes",
        Compression="lzma",
        DefaultGroupName="%(name)s",
        DefaultDirName="{autopf}\\%(name)s",  # Use autopf for auto-detection of Program Files
        OutputBaseFilename="%(name)s-%(version)s-setup",
    )
    metadata_map.update(consts_map)
    required_sections = (
        "Setup",
        "Files",
        "Run",
        "UninstallRun",
        "Languages",
        "Icons",
        "Code",
        "tasks",
        "registry",
    )
    default_flags = (
        "ignoreversion",
        "overwritereadonly",
        "uninsremovereadonly",
    )
    default_dir_flags = (
        "recursesubdirs",
        "createallsubdirs",
    )
    bin_exts = (
        ".exe",
        ".dll",
        ".pyd",
    )
    iss_metadata = {}

    def __init__(self, dist_dir, metadata, inno_script, inno_setup_exe=None, 
                 bundle_vcr=True, register_startup=False, zip_option=False, 
                 extra_inno_script=None):
        """Initialize the InnoScript with the necessary parameters.
        
        Args:
            dist_dir: Directory containing the py2exe output
            metadata: Distribution metadata object
            inno_script: Path to or content of the Inno Setup script
            inno_setup_exe: Path to the Inno Setup compiler (ISCC.exe)
            bundle_vcr: Whether to bundle VCR DLLs
            register_startup: Whether to register the app to run at startup
            zip_option: Whether to zip the setup file (True/False or filename)
            extra_inno_script: Additional Inno Setup script content
        """
        self.dist_dir = dist_dir
        self._metadata = metadata
        self.issfile = os.path.join(dist_dir, "distutils.iss")
        self.bundle_vcr = bundle_vcr
        self.register_startup = register_startup
        self.zip_option = zip_option
        
        # Handle inno_script (file path or content)
        if os.path.isfile(inno_script):
            with open(inno_script, 'r', encoding='utf-8') as f:
                self.inno_script_content = f.read()
        else:
            self.inno_script_content = inno_script
            
        if extra_inno_script:
            self.inno_script_content += f"\n{extra_inno_script}"
            
        self._inno_setup_exe = inno_setup_exe
        
        # Scan the dist directory to find files
        self.created_files = self._scan_dist_dir()

    def parse_iss(self, s):
        firstline = ""
        sectionname = ""
        lines = []
        for line in s.splitlines():
            if line.startswith("[") and "]" in line:
                if lines:
                    yield firstline, sectionname, lines
                firstline = line
                sectionname = line[1: line.index("]")].strip()
                lines = []
            else:
                lines.append(line)
        if lines:
            yield firstline, sectionname, lines

    def chop(self, filename, dirname=""):
        """get relative path"""
        if not dirname:
            dirname = self.builder.dist_dir
        if dirname[-1] not in "\\/":
            dirname += "\\"
        if filename.startswith(dirname):
            filename = filename[len(dirname):]
        # else:
        # filename = os.path.basename(filename)
        return filename

    def _scan_dist_dir(self):
        """Scan the dist directory to categorize files."""
        results = {
            'executables': [],
            'windows_exes': [],
            'com_servers': [],
            'services': [],
            'dlls': [],
            'data_files': [],
            'lib_files': [],
            'other': [],
        }
        
        # Walk through the dist directory
        for root, dirs, files in os.walk(self.dist_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()
                
                if ext == '.exe':
                    results['executables'].append(fpath)
                    # Try to determine the type of executable
                    # This is a simplistic approach - in a real implementation
                    # we would need more information from py2exe
                    if 'w' in fname.lower() or 'win' in fname.lower():
                        results['windows_exes'].append(fpath)
                elif ext in ('.dll', '.pyd'):
                    results['dlls'].append(fpath)
                    # Check if it's a COM server DLL
                    if 'com' in fname.lower():
                        results['com_servers'].append(fpath)
                    # Check if it's a service DLL
                    elif 'service' in fname.lower():
                        results['services'].append(fpath)
                else:
                    # Basic categorization for other files
                    results['data_files'].append(fpath)
                    
        return results

    @property
    def metadata(self):
        """Get metadata as a dictionary."""
        metadata = {}
        for attr in dir(self._metadata):
            if not attr.startswith('_'):
                value = getattr(self._metadata, attr, "")
                metadata[attr] = value if value is not None else ""
        return metadata

    @property
    def appid(self):
        """Generate a consistent AppID based on metadata."""
        m = self.metadata
        if m["url"]:
            src = m["url"]
        elif m["name"] and m["version"] and m["author_email"]:
            src = f"mailto:{m['author_email']}?subject={m['name']}-{m['version']}"
        elif m["name"] and m["author_email"]:
            src = f"mailto:{m['author_email']}?subject={m['name']}"
        else:
            return m["name"]
        appid = uuid.uuid5(uuid.NAMESPACE_URL, src).urn.rsplit(":", 1)[1]
        return f"{{{appid}}}"

    @property
    def iss_consts(self):
        """Get constants for the ISS file."""
        metadata = self.metadata
        return dict((k, v % metadata) for k, v in self.consts_map.items())

    @property
    def innoexepath(self):
        """Find the Inno Setup compiler executable."""
        if self._inno_setup_exe and os.path.isfile(self._inno_setup_exe):
            return self._inno_setup_exe
            
        # Try registry (prefer 64-bit view first)
        keys_to_try = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
        ]
        
        for root, key, flags in keys_to_try:
            try:
                with winreg.OpenKey(root, key, 0, flags) as handle:
                    install_location, _ = winreg.QueryValueEx(handle, "InstallLocation")
                    if install_location:
                        iscc_path = os.path.join(install_location, "ISCC.exe")
                        if os.path.isfile(iscc_path):
                            return iscc_path
            except OSError:
                continue

        # Try default Program Files locations
        for pf_var in ["ProgramFiles", "ProgramFiles(x86)"]:
            pf_path = os.environ.get(pf_var)
            if pf_path:
                iscc_path = os.path.join(pf_path, "Inno Setup 6", "ISCC.exe")
                if os.path.isfile(iscc_path):
                    return iscc_path
                    
        # Last resort - just return the filename and hope it's in PATH
        return "ISCC.exe"

    @property
    def msvcfiles(self):
        """Get MSVC runtime files if needed.
        
        Note: For modern Python (3.5+), this is usually not needed as py2exe
        handles the runtime dependencies.
        """
        # For Python 3.5+ with VS 2015 (14.0) and later, py2exe bundles the necessary
        # Universal CRT DLLs or the target system has the VCRedist installed.
        if sys.version_info >= (3, 5):
            return []  # Yield nothing for modern Python
            
        # This is legacy code for older Python versions
        import distutils.msvccompiler
        try:
            msvc_ver = distutils.msvccompiler.get_build_version()
        except AttributeError:
            # Modern Python doesn't expose this
            return []
            
        files_to_include = []
        
        # Only proceed for older MSVC versions
        if msvc_ver < 14.0:
            vcver = "%.2d" % (msvc_ver * 10,)
            try:
                # Try to find the runtime DLLs
                if hasattr(ctypes.windll, "msvcr" + vcver):
                    msvcr = getattr(ctypes.windll, "msvcr" + vcver)
                    vcrname = modname(msvcr._handle)
                    files_to_include.append(vcrname)
                
                if hasattr(ctypes.windll, "msvcp" + vcver):
                    msvcp = getattr(ctypes.windll, "msvcp" + vcver)
                    vcpname = modname(msvcp._handle)
                    files_to_include.append(vcpname)
            except (AttributeError, WindowsError):
                # If we can't load the DLLs, just continue
                pass
                
        return files_to_include

    def handle_iss(self, lines, fp):
        for line in lines:
            fp.write(line + "\n")

    def handle_iss_setup(self, lines, fp):
        metadata = self.metadata
        iss_metadata = dict((k, v % metadata)
                            for k, v in self.metadata_map.items())
        iss_metadata["OutputDir"] = self.builder.dist_dir
        iss_metadata["AppId"] = self.appid
        # add InfoBeforeFile
        for filename in (
            "README",
            "README.txt",
        ):
            if os.path.isfile(filename):
                iss_metadata["InfoBeforeFile"] = os.path.abspath(filename)
                break

        # add LicenseFile
        for filename in (
            "license.txt",
            "COPYING",
        ):
            if os.path.isfile(filename):
                iss_metadata["LicenseFile"] = os.path.abspath(filename)
                break
        # handle user operations
        user = {}
        for line in lines:
            m = re.match("\s*(\w+)\s*=\s*(.*)\s*", line)
            if m:
                name, value = m.groups()
                if name in iss_metadata:
                    del iss_metadata[name]
                user[name] = value
                fp.write(
                    "%s=%s\n"
                    % (
                        name,
                        value,
                    )
                )
            else:
                fp.write(line + "\n")

        if "AppId" in iss_metadata:
            print(
                'There is no "AppId" in "[Setup]" section.\n'
                '"AppId" is automatically generated from metadata (%s),'
                "not a random value." % iss_metadata["AppId"]
            )

        for k in sorted(iss_metadata):
            fp.write(
                (
                    "%s=%s\n"
                    % (
                        k,
                        iss_metadata[k],
                    )
                )
            )

        self.iss_metadata = {}
        self.iss_metadata.update(iss_metadata)
        self.iss_metadata.update(user)

        fp.write("\n")

    def handle_iss_files(self, lines, fp):
        """Handle the [Files] section of the ISS file."""
        files = []
        excludes = []

        # Add MSVC runtime files if needed
        if self.bundle_vcr:
            files.extend(self.msvcfiles)

        # Python 3 doesn't support Windows 9x and me
        excludes.extend(findfiles(files, "w9xpopen.exe"))

        # Add all files from the dist directory
        files.extend(self.created_files.get('executables', []))
        files.extend(self.created_files.get('dlls', []))
        files.extend(self.created_files.get('data_files', []))
        
        # Handle Tkinter if present
        if os.path.exists(os.path.join(self.dist_dir, "tcl")):
            tcl_dst_dir = os.path.join(self.dist_dir, "tcl")
            files.append(tcl_dst_dir)

        stored = set()
        for filename in files:
            if filename in excludes:
                continue
            relname = self.chop(filename)
            # user operation given or already wrote
            if relname in "".join(lines) or relname in stored:
                continue

            flags = list(self.default_flags)
            place = ""

            if os.path.isfile(filename):
                if os.path.splitext(relname)[1].lower() in self.bin_exts:
                    flags.append("restartreplace")
                    flags.append("uninsrestartdelete")

                if filename.startswith(self.dist_dir):
                    place = os.path.dirname(relname)

                extraargs = {}
            else:  # isdir
                if filename.startswith(self.dist_dir):
                    place = relname
                relname += "\\*"
                flags.extend(self.default_dir_flags)

            fp.issline(
                Source=relname,
                DestDir="{app}\\%s" % place,
                Flags=" ".join(flags),
                **extraargs,
            )
            stored.add(relname)

        self.handle_iss(lines, fp)

    def _iter_bin_files(self, category, lines=[]):
        """Iterate over binary files of a specific category."""
        for filename in self.created_files.get(category, []):
            relname = self.chop(filename)
            if relname in "".join(lines):
                continue
            yield filename, relname

    def handle_iss_run(self, lines, fp):
        """Handle the [Run] section of the ISS file."""
        # Process COM servers
        for _, filename in self._iter_bin_files("com_servers", lines):
            if filename.lower().endswith(".exe"):
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="/register",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Registering %s..." % os.path.basename(filename),
                )

        # Process services
        for _, filename in self._iter_bin_files("services", lines):
            # Assume pywin32 style by default
            cmdline_style = "pywin32"
            
            if cmdline_style == "py2exe":
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="-install -auto",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Registering %s..." % os.path.basename(filename),
                )
            elif cmdline_style == "pywin32":
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="--startup auto install",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Registering %s..." % os.path.basename(filename),
                )
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="start",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Starting %s..." % os.path.basename(filename),
                )
                
        self.handle_iss(lines, fp)

    def handle_iss_uninstallrun(self, lines, fp):
        """Handle the [UninstallRun] section of the ISS file."""
        # Process COM servers
        for _, filename in self._iter_bin_files("com_servers", lines):
            if filename.lower().endswith(".exe"):
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="/unregister",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Unregistering %s..." % os.path.basename(filename),
                )

        # Process services
        for _, filename in self._iter_bin_files("services", lines):
            # Assume pywin32 style by default
            cmdline_style = "pywin32"
            
            if cmdline_style == "py2exe":
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="-remove",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Unregistering %s..." % os.path.basename(filename),
                )
            elif cmdline_style == "pywin32":
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="stop",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Stopping %s..." % os.path.basename(filename),
                )
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="remove",
                    WorkingDir="{app}",
                    Flags="runhidden",
                    StatusMsg="Unregistering %s..." % os.path.basename(filename),
                )
                
        self.handle_iss(lines, fp)

    def handle_iss_icons(self, lines, fp):
        """Handle the [Icons] section of the ISS file."""
        # Find the main executable to use for shortcuts
        main_exe = None
        for _, filename in self._iter_bin_files("windows_exes", lines):
            main_exe = filename
            fp.issline(
                Name="{group}\\%s" % self.metadata["name"],
                Filename="{app}\\%s" % filename,
            )
            break
            
        # If no windows exe was found, try to use any executable
        if not main_exe:
            for _, filename in self._iter_bin_files("executables", lines):
                main_exe = filename
                fp.issline(
                    Name="{group}\\%s" % self.metadata["name"],
                    Filename="{app}\\%s" % filename,
                )
                break

        # Add uninstall shortcut
        if main_exe:
            fp.issline(
                Name="{group}\\Uninstall %s" % self.metadata["name"],
                Filename="{uninstallexe}",
            )
            
            # Desktop icon (optional via task)
            fp.issline(
                Name="{commondesktop}\\%s" % self.metadata["name"],
                Filename="{app}\\%s" % main_exe,
                WorkingDir="{app}",
                Tasks="desktopicon",
            )
            
        self.handle_iss(lines, fp)

    def handle_iss_tasks(self, lines, fp):
        """Handle the [Tasks] section of the ISS file."""
        fp.issline(
            Name="desktopicon",
            Description="{cm:CreateDesktopIcon}",
            GroupDescription="{cm:AdditionalIcons}",
            Flags="unchecked",  # Default to unchecked
        )
        if self.register_startup:
            fp.issline(
                Name="startup", 
                Description="Run at startup",
                Flags="unchecked",
            )
            
        self.handle_iss(lines, fp)

    def handle_iss_registry(self, lines, fp):
        """Handle the [Registry] section of the ISS file."""
        if self.register_startup:
            # Find the main executable
            main_exe = None
            for filename in self.created_files.get('windows_exes', []):
                main_exe = os.path.basename(filename)
                break
                
            if not main_exe and self.created_files.get('executables', []):
                main_exe = os.path.basename(self.created_files['executables'][0])
                
            if main_exe:
                fp.issline(
                    Root="HKCU",
                    Subkey="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                    ValueType="string",
                    ValueName=self.metadata["name"],
                    ValueData="{app}\\%s" % main_exe,
                    Flags="uninsdeletevalue",
                    Tasks="startup",
                )
                
        self.handle_iss(lines, fp)

    def handle_iss_languages(self, lines, fp):
        self.handle_iss(lines, fp)

        if lines:
            return

        innopath = os.path.dirname(self.innoexepath)
        for root, dirs, files in os.walk(innopath):
            for basename in files:
                if not basename.lower().endswith(".isl"):
                    continue
                filename = self.chop(os.path.join(root, basename), innopath)
                fp.issline(
                    Name=os.path.splitext(basename)[0],
                    MessagesFile="compiler:%s" % filename,
                )

    def handle_iss_code(self, lines, fp):
        self.handle_iss(lines, fp)
        fp.write(DEFAULT_CODES)

    def create(self):
        """Create the Inno Setup script file."""
        fp = IssFile(self.issfile, "wt")
        fp.write('; This file is created by py2exe InnoSetup extension.\n')

        # write "#define CONSTANT value"
        consts = self.iss_consts
        consts.update(
            {
                "PYTHON_VERSION": "%d.%d" % sys.version_info[:2],
                "PYTHON_VER": "%d%d" % sys.version_info[:2],
                "PYTHON_DIR": sys.prefix,
                "PYTHON_DLL": os.path.basename(sys.executable),
            }
        )
        consts.update((k.upper(), v) for k, v in self.metadata.items())
        for k in sorted(consts):
            if consts[k]:  # Only write non-empty values
                fp.write('#define %s "%s"\n' % (k, consts[k]))

        fp.write("\n")

        # handle sections
        sections = set()
        for firstline, name, lines in self.parse_iss(self.inno_script_content):
            if firstline:
                fp.write(firstline + "\n")
            handler = getattr(self, "handle_iss_%s" % name.lower(), self.handle_iss)
            handler(lines, fp)
            fp.write("\n")
            sections.add(name)

        # Add any missing required sections
        for name in self.required_sections:
            if name.lower() not in [s.lower() for s in sections]:
                fp.write("[%s]\n" % name)
                handler = getattr(self, "handle_iss_%s" % name.lower(), self.handle_iss)
                handler([], fp)
                fp.write("\n")

    def compile_script(self):
        """Compile the Inno Setup script into an installer."""
        try:
            subprocess.check_call([self.innoexepath, self.issfile])
        except (WindowsError, subprocess.CalledProcessError) as e:
            raise EnvironmentError(
                f"Failed to compile the installer: {e}\n"
                "Please ensure InnoSetup 6+ is installed correctly."
            )
        setupfile = self.setup_file_path

        # zip the setup file if requested
        if self.zip_option:
            if isinstance(self.zip_option, str):
                zipname = self.zip_option
            else:
                zipname = setupfile + ".zip"

            with ZipFile(zipname, "w", ZIP_DEFLATED, allowZip64=True) as zip_file:
                zip_file.write(setupfile, os.path.basename(setupfile))
                
            print(f"Created zip file: {zipname}")
            return zipname
        else:
            print(f"Created installer: {setupfile}")
            return setupfile

    @property
    def setup_file_path(self):
        return os.path.join(
            self.output_dir,
            self.iss_metadata.get("OutputBaseFilename", "setup") + ".exe",
        )

    @property
    def output_dir(self):
        return self.iss_metadata.get(
            "OutputDir", os.path.join(os.path.dirname(self.issfile), "Output")
        )


class innosetup(distutils.core.Command):
    """Create an installer using Inno Setup."""
    
    description = "create an executable installer using Inno Setup"
    
    user_options = [
        ("inno-setup-exe=", None, "path to InnoSetup compiler (ISCC.exe)"),
        ("inno-script=", None, "path to InnoSetup script file or script content"),
        ("extra-inno-script=", None, "additional InnoSetup script content"),
        ("certificate-file=", None, "path to signing certificate"),
        ("certificate-password=", None, "password for signing certificate"),
        ("extra-sign=", None, "extra files to be signed"),
        ("bundle-vcr=", None, "bundle MSVC runtime DLLs (usually not needed)"),
        ("zip=", None, "zip the setup file (True/False or filename)"),
        ("register-startup=", None, "register application to run at startup"),
        ("dist-dir=", "d", "directory to put final built distributions in"),
    ]
    
    boolean_options = ["bundle_vcr", "zip", "register_startup"]

    def initialize_options(self):
        """Initialize command options."""
        self.inno_setup_exe = None
        self.inno_script = DEFAULT_ISS
        self.extra_inno_script = None
        self.certificate_file = None
        self.certificate_password = None
        self.extra_sign = []
        self.bundle_vcr = False  # Default to False for modern Python
        self.zip = False
        self.register_startup = False
        self.dist_dir = None
        
    def finalize_options(self):
        """Finalize command options."""
        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))
        if self.dist_dir is None:
            self.dist_dir = "dist"
            
        # Convert string options to appropriate types
        if isinstance(self.zip, str) and self.zip.lower() in ('0', 'false', 'no'):
            self.zip = False
        elif isinstance(self.zip, str) and self.zip.lower() in ('1', 'true', 'yes'):
            self.zip = True
            
        if isinstance(self.bundle_vcr, str) and self.bundle_vcr.lower() in ('0', 'false', 'no'):
            self.bundle_vcr = False
        elif isinstance(self.bundle_vcr, str) and self.bundle_vcr.lower() in ('1', 'true', 'yes'):
            self.bundle_vcr = True
            
        if isinstance(self.register_startup, str) and self.register_startup.lower() in ('0', 'false', 'no'):
            self.register_startup = False
        elif isinstance(self.register_startup, str) and self.register_startup.lower() in ('1', 'true', 'yes'):
            self.register_startup = True
            
        # Ensure extra_sign is a list
        if isinstance(self.extra_sign, str):
            self.extra_sign = [self.extra_sign]

    def _find_inno_setup(self):
        """Find the Inno Setup compiler."""
        if self.inno_setup_exe and os.path.isfile(self.inno_setup_exe):
            return self.inno_setup_exe
            
        # Try registry (prefer 64-bit view first)
        keys_to_try = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1", winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
        ]
        
        for root, key, flags in keys_to_try:
            try:
                with winreg.OpenKey(root, key, 0, flags) as handle:
                    install_location, _ = winreg.QueryValueEx(handle, "InstallLocation")
                    if install_location:
                        iscc_path = os.path.join(install_location, "ISCC.exe")
                        if os.path.isfile(iscc_path):
                            return iscc_path
            except OSError:
                continue

        # Try default Program Files locations
        for pf_var in ["ProgramFiles", "ProgramFiles(x86)"]:
            pf_path = os.environ.get(pf_var)
            if pf_path:
                iscc_path = os.path.join(pf_path, "Inno Setup 6", "ISCC.exe")
                if os.path.isfile(iscc_path):
                    return iscc_path
                    
        return None  # Not found

    def run(self):
        """Run the command: build the installer."""
        # First, run py2exe to create the executable
        self.run_command('py2exe')
        py2exe_cmd = self.get_finalized_command('py2exe')
        
        # Find Inno Setup
        inno_exe_path = self._find_inno_setup()
        if not inno_exe_path:
            raise EnvironmentError(
                "Could not find Inno Setup 6 compiler (ISCC.exe). "
                "Please install Inno Setup 6 or specify the path using --inno-setup-exe."
            )
        print(f"Using Inno Setup compiler: {inno_exe_path}")
        
        # Prepare the Inno Setup script
        inno_script_content = ""
        if self.inno_script and os.path.isfile(self.inno_script):
            with open(self.inno_script, 'r', encoding='utf-8') as f:
                inno_script_content = f.read()
        elif self.inno_script:  # Assume it's a string
            inno_script_content = self.inno_script
        else:
            inno_script_content = DEFAULT_ISS  # Use default if none provided
            
        if self.extra_inno_script:
            inno_script_content += f"\n{self.extra_inno_script}"
            
        # Create the InnoScript instance
        script = InnoScript(
            dist_dir=self.dist_dir,
            metadata=self.distribution.metadata,
            inno_script=inno_script_content,
            inno_setup_exe=inno_exe_path,
            bundle_vcr=self.bundle_vcr,
            register_startup=self.register_startup,
            zip_option=self.zip,
            extra_inno_script=self.extra_inno_script
        )
        
        # Sign executables if requested
        if self.certificate_file:
            self.sign_executables()
            
        # Create and compile the script
        print("*** creating the inno setup script ***")
        script.create()
        print("*** compiling the inno setup script ***")
        setup_file = script.compile_script()
        
        # Sign the installer if requested
        if self.certificate_file:
            self.sign_executable(setup_file)

    def sign_executables(self):
        """Sign all executables in the dist directory."""
        # Find all executables in the dist directory
        for root, _, files in os.walk(self.dist_dir):
            for file in files:
                if file.lower().endswith('.exe'):
                    self.sign_executable(os.path.join(root, file))
                    
        # Sign any extra files specified
        if self.extra_sign:
            for extra in self.extra_sign:
                self.sign_executable(os.path.join(self.dist_dir, extra))

    def sign_executable(self, exepath):
        """Sign a single executable."""
        if not os.path.exists(exepath):
            self.warn(f"File to sign not found: {exepath}")
            return
            
        url = self.distribution.get_url()
        try:
            signtool.sign(
                exepath,
                url=url,
                certificate_file=self.certificate_file,
                certificate_password=self.certificate_password,
            )
            print(f"Signed: {exepath}")
        except Exception as e:
            self.warn(f"Failed to sign {exepath}: {e}")


# Register the command with distutils
distutils.command.__all__.append("innosetup")
sys.modules["distutils.command.innosetup"] = sys.modules[__name__]


if __name__ == "__main__":
    sys.modules["innosetup"] = sys.modules[__name__]
    from distutils.core import setup

    setup(
        name="innosetup",
        version="0.6.3",
        license="PSF",
        description=__doc__.splitlines()[0],
        long_description=__doc__,
        author="chrono-meter@gmx.net",
        author_email="chrono-meter@gmx.net",
        url="http://pypi.python.org/pypi/innosetup",
        platforms="win32, win64",
        classifiers=[
            # 'Development Status :: 4 - Beta',
            "Development Status :: 5 - Production/Stable",
            "Environment :: Win32 (MS Windows)",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: Python Software Foundation License",
            "Operating System :: Microsoft :: Windows :: Windows NT/2000",
            "Programming Language :: Python",
            "Topic :: Software Development :: Build Tools",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        py_modules=[
            "innosetup",
        ],
    )
