
"""
All symbols in this module are in the global namespace of imported project scripts.
"""

import glob, os.path, sys

from devon.makers.ctags import CTags
from devon.makers.mozilla import FirefoxExtension, XPIDLCompile
from devon.makers.python import PythonModules, LinkPythonModule
from devon.makers.flexbison import FlexParse, BisonParse
from devon.makers.configuremake import ConfigureMake
from devon.projects import ExternalProject

if sys.platform == "darwin":
    from devon.makers.mac.appBundle import AppBundle
    from devon.makers.mac.installer import Installer
    from devon.makers.mac.diskImage import DiskImage
    from devon.makers.unix.compile import Compile, CompileTestRunner
    from devon.makers.unix.link import \
        LinkExecutable, LinkStaticLib, LinkDynamicLib, LinkTestRunner

elif sys.platform in ("cygwin", "win32"):
    from devon.makers.win.compile import Compile, CompileTypeLibraries, CompileInterfaces, CompileResources, CompileTestRunner
    from devon.makers.win.link import \
        LinkExecutable, LinkStaticLib, LinkDynamicLib, LinkTestRunner

else:
    from devon.makers.unix.compile import Compile, CompileTestRunner
    from devon.makers.unix.link import \
        LinkExecutable, LinkStaticLib, LinkDynamicLib, LinkTestRunner
           
# **************************************************************************************************

from devon.projects import defaultCompilerFlags, defaultLinkerFlags

system = sys.platform
platform = None
sdk = None
arch = None

# **************************************************************************************************

def findFiles(rootPath, pattern):
    """Convenience function to recursively search for files that match a pattern"""
    
    def searchDir(rootPath, pattern, matches=None):
        if not matches:
            matches = []
        
        found = glob.glob(os.path.join(rootPath, pattern))
        if found:
            matches += found
            
        names = os.listdir(rootPath)
        for name in names:
            fullPath = os.path.join(rootPath, name)
            if os.path.isdir(fullPath) and not name[0] == ".":
                matches = searchDir(fullPath, pattern, matches)
                
        return matches
    
    if os.path.isdir(rootPath):
        return searchDir(rootPath, pattern)
