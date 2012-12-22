import setuptools
import platform
import shutil
if platform.system == "Windows":
 import py2exe
import innosetup

class InstallerBuilder(object):
 build_dirs = ['build', 'dist', 'release', 'update']
 default_dll_excludes = ["powrprof.dll", "mswsock.dll"]

 def __init__(self, main_module=None, name=None, version=None, url=None, author=None, author_email=None, datafiles=None, compressed=False, optimization_level=1, py2exe_datafile_packages=[]):
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
  self.compressed = compressed
  self.optimization_level = optimization_level
  self.py2exe_datafile_packages = ['innosetup'] + py2exe_datafile_packages

 def build(self):
  self.remove_previous_build()
  self.build_installer()


 def remove_previous_build(self):
  for directory in self.build_dirs:
   shutil.rmtree(directory, ignore_errors=True)

 def find_datafiles(self):
  datafiles = []
  for package in self.py2exe_datafile_packages:
   pkg = __import__(package)
   datafiles.extend(pkg.py2exe_datafiles())
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
     'dll_excludes': self.default_dll_excludes,
     'optimize': self.optimization_level,
     'skip_archive': True,
    },
    'py2app': {
     'argv_emulation': True,
     'app': [self.main_module],
    }
   },
   windows = [{
    'script': self.main_module,
    'dest_base': self.name,
   }],
  )
