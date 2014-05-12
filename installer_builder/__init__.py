import setuptools
import __builtin__
import collections
import datetime
import glob
import importlib
import platform
import shutil
import subprocess
import time
import os
if platform.system() == "Windows":
 import installer_builder.innosetup
if platform.system() == 'Darwin':
 import py2app.build_app

if '_' not in __builtin__.__dict__:
 __builtin__.__dict__['_'] = lambda x: x
 __builtin__.__dict__['__'] = lambda x: x
 __builtin__.__dict__['lngettext'] = lambda *a: [i for i in a]

__version__ = 0.382

class InstallerBuilder(object):
 build_dirs = ['build', 'dist']
 dist_dir = 'dist'
 locale_dir = 'locale'
 default_dll_excludes = ['mpr.dll', 'powrprof.dll', 'mswsock.dll']
 default_excludes = ['bdb', 'doctest', 'email.test', 'pdb', 'pywin.dialogs', 'win32pipe', 'win32wnet', 'win32com.gen_py', ]
 update_archive_format = 'zip'
 build_command = 'release'


 def __init__(self, main_module=None, name=None, version=None, url=None, author=None, author_email=None, datafiles=None, includes=None, excludes=None, compressed=False, skip_archive=False, bundle_level=3, optimization_level=1, extra_packages=None, datafile_packages=None, output_directory='release', create_update=False, postbuild_commands=None, osx_frameworks=None, extra_inno_script=None, register_startup=False, localized_packages=None, has_translations=False):
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
  self.excludes = excludes
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
  self.postbuild_commands = collections.defaultdict(list)
  self.postbuild_commands.update(postbuild_commands)
  if osx_frameworks is None:
   osx_frameworks = []
  self.osx_frameworks = osx_frameworks
  self.extra_inno_script = extra_inno_script
  self.build_start_time = None
  self.register_startup = register_startup
  if localized_packages is None:
   localized_packages = []
  self.localized_packages = localized_packages
  self.has_translations = has_translations

 def build(self):
  self.build_start_time = time.time()
  self.prebuild_message()
  self.remove_previous_build()
  self.build_installer()
  self.finalize_build()
  self.perform_postbuild_commands()
  self.report_build_statistics()

 def prebuild_message(self):
  print "Installer builder version %s" % __version__
  print "Building %s installer for %s %s" % (platform.system(), self.name, self.version)

 def remove_previous_build(self):
  print "Removing previous output directories"
  directories = self.build_dirs + [self.output_directory]
  for directory in directories:
   print "Deleting %s" % directory
   shutil.rmtree(directory, ignore_errors=True)
   print "Deleted ", directory

 def find_datafiles(self):
  datafiles = []
  for package in self.datafile_packages:
   pkg = importlib.import_module(package)
   datafiles.extend(pkg.find_datafiles())
  if self.has_translations:
   datafiles.extend(self.find_application_language_data())
   datafiles.extend(self.find_babel_datafiles())
  for package in self.localized_packages:
   pkg = importlib.import_module(package)
   path = pkg.__path__[0]
   locale_path = os.path.join(path, self.locale_dir)
   files = self.find_locale_data(locale_path)
   datafiles.extend(list(files))
   print "Added locale data for %s" % package
  return self.datafiles + datafiles

 def find_application_language_data(self):
  for directory, filenames in self.find_locale_data(self.locale_dir):
   yield directory, filenames

 def find_babel_datafiles(self):
  import babel
  return ('localedata', glob.glob(os.path.join(babel.__path__[0], 'localedata', '*.*'))),

 def find_locale_data(self, locale_path):
  for dirpath, dirnames, filenames in os.walk(locale_path):
   files = []
   for filename in filenames:
    path = os.path.join(dirpath, filename)
    if filename.lower().endswith('.mo'):
     files.append(path)
   if files:
    directory = os.path.join(self.locale_dir, os.path.relpath(dirpath, start=locale_path))
    yield directory, files


 def finalize_build(self):
  print "Finalizing build..."
  if platform.system() == 'Darwin':
   self.remove_embedded_interpreter()
   self.shrink_mac_binaries()
   self.lipo_file(os.path.join(self.get_app_path(), self.name))
   self.create_dmg()
  self.move_output()
  if self.create_update:
   self.create_update_archive()


 def remove_embedded_interpreter(self):
  print "Replacing the embedded interpreter with a dumby file"
  interpreter_path = os.path.join(self.get_app_path(), 'python')
  os.remove(interpreter_path)
  self.execute_command('touch %s' % interpreter_path)
  self.execute_command('chmod +x %s' % interpreter_path)

 def get_app_path(self):
  if platform.system() == 'Darwin':
   return os.path.join(self.dist_dir, '%s.app' % self.name, 'Contents', 'MacOS')
  return self.dist_dir

 def create_dmg(self):
  print "Creating .dmg disk image"
  self.execute_command(   'hdiutil create -srcfolder dist/%s.app -size 150m dist/%s' % (self.name, self.installer_filename()))

 def move_output(self):
  os.mkdir(self.output_directory)
  destination = os.path.join(self.output_directory, self.installer_filename())
  os.rename(self.find_created_installer(), destination)
  print "Moved generated installer to %s" % destination

 def create_update_archive(self):
  print "Generating update archive"
  name = '%s-%s-%s' % (self.name, self.version, platform.system())
  root_dir = self.dist_dir
  if platform.system() == 'Darwin':
   root_dir = os.path.join(root_dir, '%s.app' % self.name)
  filename = shutil.make_archive(name, self.update_archive_format, root_dir=root_dir)
  filename = os.path.split(filename)[-1]
  destination = os.path.join(self.output_directory, filename)
  os.rename(filename, destination)
  print "Generated update archive filename: %s" % destination

 def find_created_installer(self):
  res = os.path.join('dist', self.installer_filename())
  if not os.path.exists(res):
   res = os.path.join(self.output_directory, self.installer_filename())
   if not os.path.exists(res):
    raise RuntimeError("Installer %s does not exist" % res)
  return res

 def installer_filename(self):
  if platform.system() == 'Windows':
   return '%s-%s-setup.exe' % (self.name, self.version)
  elif platform.system() == 'Darwin':
   return '%s-%s.dmg' % (self.name, self.version)

 def get_command_class(self):
  if platform.system() == 'Windows':
   return installer_builder.innosetup.innosetup
  elif platform.system() == 'Darwin':
   return py2app.build_app.py2app

 def perform_postbuild_commands(self):
  if not self.postbuild_commands[platform.system().lower()]:
   return
  print "Performing postbuild commands for platform %s" % platform.system()
  for command in self.postbuild_commands[platform.system().lower()]:
   self.execute_command(command)

 def execute_command(self, command):
  subprocess.check_call([command], shell=True)

 def report_build_statistics(self):
  print "Generated installer filename: %s" % self.find_created_installer()
  print "Generated installer filesize: %s" % format_filesize(os.stat(self.find_created_installer()).st_size)
  self.report_build_time()

 def shrink_mac_binaries(self):
  shrink_extensions = ('.dylib', '.so')
  for basepath, dirs, files in os.walk(self.dist_dir):
   for file in files:
    if os.path.splitext(file)[-1] in shrink_extensions:
     path = os.path.join(basepath, file)
     self.lipo_file(path)

 def lipo_file(self, filename):
  self.execute_command('lipo -thin i386 %s -output %s' % (filename, filename))
  print "Lipoed file %s" % filename

 def report_build_time(self):
  build_time = time.time() - self.build_start_time
  td = datetime.timedelta(seconds=build_time)
  print "Build completed in ", format(td)

 def build_installer(self):
  if None in (self.name, self.main_module):
   raise RuntimeError("Insufficient information provided to build")
  res = setuptools.setup(
   name = self.name,
   author = self.author,
   author_email = self.author_email,
   url = self.url,
   version = self.version,
   packages = setuptools.find_packages(),
   data_files = self.find_datafiles(),
   app = [self.main_module],
   options = {
    'py2exe': {
     'compressed': self.compressed,
     'bundle_files': self.bundle_level,
     'includes': self.includes,
     'excludes': self.excludes,
     'packages': self.extra_packages,
     'dll_excludes': self.default_dll_excludes,
     'optimize': self.optimization_level,
     'skip_archive': self.skip_archive,
    },
    'innosetup': {
     'extra_inno_script': self.extra_inno_script,
     'register_startup': self.register_startup,
    },
    'py2app': {
     'compressed': self.compressed,
     'includes': self.includes + self.extra_packages,
     'excludes': self.excludes,
     'frameworks': self.osx_frameworks,
     'optimize': self.optimization_level,
     'argv_emulation': True,
     'plist': {
      'CFBundleName': self.name,
      'CFBundleShortVersionString': self.version,
      'CFBundleGetInfoString': '%s %s' % (self.name, self.version),
      'CFBundleExecutable': self.name,
     },
    },
   },
   windows = [{
    'script': self.main_module,
    'dest_base': self.name,
    'company_name': self.author,
   }],
   cmdclass = {self.build_command: self.get_command_class()},
  )

class AppInstallerBuilder(InstallerBuilder):

 def __init__(self, application=None, **kwargs):
  self.application = application
  new_kwargs = {}
  new_kwargs['name'] = application.name
  new_kwargs['version'] = getattr(application, 'version', None)
  new_kwargs['url'] = getattr(application, 'website', None)
  new_kwargs['author'] = getattr(application, 'author', None)
  datafiles = kwargs.get('datafiles', [])
  datafile_packages = kwargs.get('datafile_packages', [])
  includes = kwargs.get('includes', [])
  has_translations = kwargs.get('has_translations', False)
  if has_translations:
   includes.append('babel.plural')
  extra_packages = kwargs.get('extra_packages', [])
  localized_packages = kwargs.get('localized_packages', [])
  config_spec = getattr(application, 'config_spec', None)
  if config_spec is True:
   config_spec = "%s.confspec" % application.name
  if config_spec is not None:
   datafiles.extend([('', [config_spec])])
  import babel
  datafiles.extend([('babel', [os.path.join(babel.__path__[0], 'global.dat')])])
  from requests import __file__ as requests_path
  datafiles.extend([('', [os.path.join(os.path.dirname(requests_path), 'cacert.pem')])])
  kwargs['datafiles'] = datafiles
  if hasattr(application, 'output'):
   datafile_packages.append('accessible_output2')
  if hasattr(application, 'sound') or hasattr(application, 'UI_sounds'):
   datafile_packages.append('sound_lib')
  if hasattr(application, 'update_endpoint'):
   datafile_packages.append('autoupdate')
   new_kwargs['create_update'] = True
  kwargs['datafile_packages'] = datafile_packages
  includes = kwargs.get('includes', [])
  if hasattr(application, 'activation_module'):
   extra_packages.append('product_key') #Because it's not picked up on OSX.
   includes.append(application.activation_module)
  kwargs['extra_packages'] = extra_packages
  if hasattr(application, 'activation_module'):
   localized_packages.append('product_key')
  if hasattr(application, 'main_window_class'):
   localized_packages.append('wx')
   localized_packages.append('app_elements')
   if isinstance(application.main_window_class, basestring):
    includes.append('.'.join(application.main_window_class.split('.')[:-1]))
  kwargs['localized_packages'] = localized_packages
  kwargs['includes'] = includes
  new_kwargs.update(kwargs)
  if hasattr(application, 'register_startup'):
   new_kwargs['register_startup'] = application.register_startup
  if hasattr(application, 'debug_port') or hasattr(application, 'debug_host'):
   includes.append('SocketServer') #not picked up on Mac
  new_kwargs['includes'] = includes
  super(AppInstallerBuilder, self).__init__(**new_kwargs)


def format_filesize(num):
 for x in ['bytes','KB','MB','GB','TB']:
  if num < 1024.0:
   return "%3.1f %s" % (num, x)
  num /= 1024.0

def standard_wx_excludes():
 return ['wx.py', 'wx.stc', ]

def sqlite_sqlalchemy_excludes():
 return ['sqlalchemy.testing', 'sqlalchemy.dialects.postgresql', 'sqlalchemy.dialects.mysql', 'sqlalchemy.dialects.oracle', 'sqlalchemy.dialects.mssql', 'sqlalchemy.dialects.firebird', 'sqlalchemy.dialects.sybase', 'sqlalchemy.dialects.drizzle', ]

def app_framework_excludes():
 return ['watchdog', 'yappi', 'pytest', 'pyreadline', 'nose', ]

def stdlib_excludes():
 return ['email.test', 'ftplib', 'tarfile', ]

def win32_excludes():
 return ['win32pipe', 'win32wnet', ]
