
import os.path, sys

# **************************************************************************************************

# XXXblake Shouldn't have to duplicate here what's in devon/project.dev
if sys.platform == "darwin":
    appPath = "/Library/Application Support/Devon"
    binPath = "%s/bin" % appPath

elif sys.platform == "win32":
    appPath = "c:\\Progra~1\\Devon"
    binPath = "%s\\bin" % appPath

    # On Windows, wrap os.path.join to use forward rather than back slashes. The os module does
    # support a "sep" variable that identifies this per-platform, but stupid os.path.join hardcodes
    # \\.
      
    def slashWrapper(oldFunc):
        def func(a, *p):
            return oldFunc(a, *p).replace("\\", "/")
        return func
    
    os.path.join = slashWrapper(os.path.join)
    os.path.normpath = slashWrapper(os.path.normpath)
    os.sep = "/"

    def symlink(linkTarget, linkPath):
        os.system("ln %s %s" % (linkTarget, linkPath))
    os.symlink = symlink

else:
    appPath = "/devon"
    binPath = "%s/bin" % appPath
