from setuptools import setup, find_packages
from installer_builder import __doc__, __version__
import os


__name__ = "installer_builder"


setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 packages = find_packages(),
 install_requires = [
  'distribute <= 0.6.49',
 ],
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries',
 ],
)
