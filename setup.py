from setuptools import setup, find_packages
import os


__name__ = "installer_builder"
__version__ = 0.381
__doc__ = """Easily generate installers for multiple platforms"""



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
