
import os.path, sys

# **************************************************************************************************

srcPath = os.environ.get("DEVON_SRCPATH")
webPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "web"))

if sys.platform == "darwin":
    userPath = os.path.expanduser("~/Library/Application Support/Devon")
    
elif sys.platform == "win32":
    userPath = "c:\\Progra~1\\Devon"

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
        os.system('ln "%s" "%s"' % (linkTarget, linkPath))
    os.symlink = symlink

else:
    userPath = os.path.expanduser("~/.devon")

