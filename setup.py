from setuptools import setup, find_packages
import os
import sys
install_requires = ['py2exe']
if int(sys.version[0]) < 3:
 install_requires = ['py2exe_py2']

__name__ = "installer_builder"
__version__ = 0.396
__doc__ = """Easily generate installers for multiple platforms"""

setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 packages = find_packages(),
 install_requires = install_requires,
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries',
 ],
)
