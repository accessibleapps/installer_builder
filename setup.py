from setuptools import setup, find_packages
import os

__name__ = "installer_builder"
__version__ = "0.2"
__doc__ = """Easily generate installers for multiple platforms"""

setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 packages = find_packages(),
 data_files = [('installer_builder/lib', [os.path.join("installer_builder", "lib", "libstdc++-6.dll"), os.path.join('installer_builder', 'lib', 'libgcc_s_dw2-1.dll')])],
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
