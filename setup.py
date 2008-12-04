
import os.path, sys
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
from distutils.command.install_data import install_data

# **************************************************************************************************

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
len_root_dir = len(root_dir)
devon_dir = os.path.join(root_dir, 'devon')

for dirpath, dirnames, filenames in os.walk(devon_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        package = dirpath[len_root_dir:].lstrip('/').replace('/', '.')
        packages.append(package)
    else:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

# **************************************************************************************************

class darwin_install_data(install_data): 
    def finalize_options (self): 
        self.set_undefined_options('install',  ('install_lib', 'install_dir')) 
        install_data.finalize_options(self) 

if sys.platform == "darwin": 
    cmdclasses = {'install_data': darwin_install_data } 
else: 
    cmdclasses = {'install_data': install_data } 

# **************************************************************************************************

setup(
    name = "Devon",
    version = "0.1",
    description = "A lightweight cross-platform development environment",
    url = "http://www.github.com/joehewitt/devon/",
    
    author = "Joe Hewitt",
    author_email = "joe@joehewitt.com",
    
    cmdclass = cmdclasses,
    packages = packages,
    data_files = data_files
)
