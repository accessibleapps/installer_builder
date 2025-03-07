from setuptools import setup, find_packages
import sys
import os

install_requires = []
if sys.platform == 'win32':
 if int(sys.version[0]) < 3:
  install_requires = ['py2exe_py2', 'pywin32']
 else:
  install_requires = ['py2exe', 'pywin32']

__name__ = "installer_builder"
__version__ = "1.5.0"
__doc__ = """Easily generate installers for multiple platforms"""

# Read the long description from README.md
long_description = __doc__
if os.path.exists('README.md'):
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
 name = __name__,
 version = __version__,
 description = __doc__,
 long_description = long_description,
 long_description_content_type = 'text/markdown',
 packages = find_packages(),
 install_requires = install_requires,
 classifiers = [
  'Development Status :: 4 - Beta',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries',
  'License :: OSI Approved :: MIT License',
  'Operating System :: Microsoft :: Windows',
  'Operating System :: MacOS :: MacOS X',
 ],
 python_requires='>=2.5',
 url='https://github.com/yourusername/installer_builder',
)
