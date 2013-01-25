import setuptools
import datetime
import importlib
import platform
import shutil
import time
if platform.system() == "Windows":
 import py2exe
 import installer_builder.innosetup

class InstallerBuilder(object):
 build_dirs = ['build', 'dist', 'release', 'update']
 default_dll_excludes = ['mpr.dll', 'powrprof.dll', 'mswsock.dll']

 def __init__(self, main_module=None, name=None, version=None, url=None, author=None, author_email=None, datafiles=None, includes=None, excludes=None, compressed=False, skip_archive=False, bundle_level=3, optimization_level=1, extra_packages=None, datafile_packages=None):
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
  self.build_start_time = None

 def build(self):
  self.build_start_time = time.time()
  self.remove_previous_build()
  self.build_installer()
  self.report_build_statistics()

 def remove_previous_build(self):
  print "Removing previous output directories"
  for directory in self.build_dirs:
   shutil.rmtree(directory, ignore_errors=True)
   print "Deleted ", directory

 def find_datafiles(self):
  datafiles = []
  for package in self.datafile_packages:
   pkg = importlib.import_module(package)
   datafiles.extend(pkg.find_datafiles())
  return self.datafiles + datafiles

 def report_build_statistics(self):
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
     'optimize': self.optimization_level,
     'argv_emulation': True,
     'app': [self.main_module],
    }
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

