import setuptools
import collections
import datetime
import importlib
import platform
import shutil
import subprocess
import time
import os
if platform.system() == "Windows":
 import py2exe
 import installer_builder.innosetup

__version__ = 0.3


class InstallerBuilder(object):
 build_dirs = ['build', 'dist', 'update']
 default_dll_excludes = ['mpr.dll', 'powrprof.dll', 'mswsock.dll']

 def __init__(self, main_module=None, name=None, version=None, url=None, author=None, author_email=None, datafiles=None, includes=None, excludes=None, compressed=False, skip_archive=False, bundle_level=3, optimization_level=1, extra_packages=None, datafile_packages=None, output_directory='release', postbuild_commands=None, osx_frameworks=None):
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
  if postbuild_commands is None:
   postbuild_commands = {}
  self.postbuild_commands = collections.defaultdict(list)
  self.postbuild_commands.update(postbuild_commands)
  if osx_frameworks is None:
   osx_frameworks = []
  self.osx_frameworks = osx_frameworks
  self.build_start_time = None

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
  print "Building %s installer..." % platform.system()

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
  return self.datafiles + datafiles

 def finalize_build(self):
  print "Finalizing build..."
  if platform.system() == 'Darwin':
   self.create_dmg()
  self.move_output()

 def create_dmg(self):
  print "Creating .dmg disk image"
  self.execute_command(   'hdiutil create -srcfolder dist/%s.app -size 150m dist/%s' % (self.name, self.installer_filename()))

 def move_output(self):
  os.mkdir(self.output_directory)
  destination = os.path.join(self.output_directory, self.installer_filename())
  os.rename(self.find_created_installer(), destination)
  print "Moved generated installer to %s" % destination


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
   }],
  )

class AppInstallerBuilder(InstallerBuilder):

 def __init__(self, application=None, **kwargs):
  self.application = application
  new_kwargs = {}
  new_kwargs['name'] = application.name
  new_kwargs['version'] = getattr(application, 'version', None)
  new_kwargs['url'] = getattr(application, 'website', None)
  datafiles = kwargs.get('datafiles', [])
  extra_packages = kwargs.get('extra_packages', [])
  config_spec = getattr(application, 'config_spec', None)
  if config_spec is True:
   config_spec = "%s.confspec" % application.name
  if config_spec is not None:
   datafiles.extend([('', [config_spec])])
  kwargs['datafiles'] = datafiles
  if hasattr(application, 'activation_module'):
   extra_packages.append('product_key') #Because it's not picked up on OSX.
   kwargs['extra_packages'] = extra_packages
  new_kwargs.update(kwargs)
  super(AppInstallerBuilder, self).__init__(**new_kwargs)


def format_filesize(num):
 for x in ['bytes','KB','MB','GB','TB']:
  if num < 1024.0:
   return "%3.1f %s" % (num, x)
  num /= 1024.0
