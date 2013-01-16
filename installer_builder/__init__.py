import setuptools
import importlib
import platform
import shutil
if platform.system() == "Windows":
 import py2exe
 import installer_builder.innosetup

class InstallerBuilder(object):
 build_dirs = ['build', 'dist', 'release', 'update']
 default_dll_excludes = ['mpr.dll', 'powrprof.dll', 'mswsock.dll']

 def __init__(self, main_module=None, name=None, version=None, url=None, author=None, author_email=None, datafiles=None, includes=None, excludes=None, compressed=False, optimization_level=1, extra_packages=None, datafile_packages=None):
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
  self.optimization_level = optimization_level
  if extra_packages is None:
   extra_packages = []
  self.extra_packages = extra_packages
  if datafile_packages is None:
   datafile_packages = []
  self.datafile_packages = datafile_packages

 def build(self):
  self.remove_previous_build()
  self.build_installer()


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

 def build_installer(self):
  if None in (self.name, self.main_module):
   raise RuntimeError("Insufficient information provided to build")
  res = setuptools.setup(
   name = self.name,
   author = self.author,
   author_email = self.author_email,
   version = self.version,
   packages = setuptools.find_packages(),
   data_files = self.find_datafiles(),
   options = {
    'py2exe': {
     'compressed': self.compressed,
     'includes': self.includes,
     'excludes': self.excludes,
     'packages': self.extra_packages,
     'dll_excludes': self.default_dll_excludes,
     'optimize': self.optimization_level,
     'skip_archive': True,
    },
    'py2app': {
     'compressed': self.compressed,
     'includes': self.includes,
     'excludes': self.excludes,
     'optimize': self.optimization_level,
     'packages': self.extra_packages,
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
  new_kwargs['url'] = getattr(application, 'url', None)
  datafiles = kwargs.get('datafiles', [])
  config_spec = getattr(application, 'config_spec', None)
  if config_spec is True:
   config_spec = "%s.confspec" % application.name
  if config_spec is not None:
   datafiles.extend([('', [config_spec])])
  kwargs['datafiles'] = datafiles
  new_kwargs.update(kwargs)
  super(AppInstallerBuilder, self).__init__(**new_kwargs)

