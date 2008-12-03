
import os.path
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

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

setup(
    name = "Devon",
    version = "0.1",
    description = "A lightweight cross-platform development environment",
    url = "http://www.github.com/joehewitt/devon/",
    
    author = "Joe Hewitt",
    author_email = "joe@joehewitt.com",
    
    packages = packages,
    data_files = data_files
)
