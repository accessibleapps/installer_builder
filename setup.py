from setuptools import setup

__name__ = "installer_builder"
__version__ = "0.1"
__doc__ = """Easily generate installers for multiple platforms"""

setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 py_modules = ['installer_builder', 'innosetup'],
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
