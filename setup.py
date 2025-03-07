from setuptools import setup, find_packages
import sys
install_requires = []
if sys.platform == 'win32':
 if int(sys.version[0]) < 3:
  install_requires = ['py2exe_py2', 'pywin32']
 else:
  install_requires = ['py2exe', 'pywin32']

__name__ = "installer_builder"
__version__ = "1.5.0"
__doc__ = """Easily generate installers for multiple platforms"""

setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 packages = find_packages(),
 install_requires = install_requires,
 classifiers = [
  'Development Status :: 4 - Beta',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries',
 ],
)
