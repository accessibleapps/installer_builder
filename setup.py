from setuptools import setup, find_packages
from installer_builder import __version__
import os


__name__ = "installer_builder"

__doc__ = """Easily generate installers for multiple platforms"""

setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 packages = find_packages(),
 install_requires = [
  'setuptools',
 ],
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries',
 ],
)
