from setuptools import setup, find_packages
import os


__name__ = "installer_builder"
__version__ = 0.382
__doc__ = """Easily generate installers for multiple platforms"""



setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 packages = find_packages(),
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries',
 ],
)
