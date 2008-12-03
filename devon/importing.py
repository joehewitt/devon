
from types import ModuleType
import os.path, glob, imp, sys

# **************************************************************************************************

NonExistent = object()

def importModule(moduleName):
    """Imports and returns a module. This works the way you would expect, unlike
       __import__, which returns the left-most module in the chain."""

    mod = __import__(moduleName)
    return sys.modules[moduleName]

def importParent(module):
    dot = module.__name__.rfind(".")
    parentName = module.__name__[0:dot] if dot != -1 else ""
    return importObject(parentName) if parentName else None

def importObject(objectName, base=None, finder=imp.find_module, loader=imp.load_module):
    """ Imports an object or module using a dot-separated path."""

    for name in objectName.split("."):
        if base:
            # First try to get the object as an attribute of the module
            child = getattr(base, name, NonExistent)
            if child is NonExistent:
                if isinstance(base, ModuleType):
                    base = _importFromModule(name, base, finder, loader)
                else:
                    raise ImportError("Unable to import %s" % objectName)
            else:
                base = child
                
        else:
            base = _importFromModule(name)
      
    return base

def importObjectModule(objectName, base=None, finder=imp.find_module, loader=imp.load_module,
    stopAtFailure=False):
    """ Imports a module from a path that may contain object references at the end, and return
        the module and the list of remaining object names."""
    
    module = base
    objectNames = objectName.split(".")
    for i in xrange(0, len(objectNames)):
        name = objectNames[i]
        if module:
            # First try to get the object as an attribute of the module
            child = getattr(module, name, NonExistent)
            if child is NonExistent:
                if isinstance(module, ModuleType):
                    if stopAtFailure:
                        try:
                            module = _importFromModule(name, module, finder, loader)
                        except ImportError,exc:
                            if module is base:
                                try:
                                    module = __import__(name)
                                except ImportError,exc:
                                    return module,objectNames[i:]
                            else:
                                return module,objectNames[i:]
                    else:
                        module = _importFromModule(name, module, finder, loader)
                else:
                    raise ImportError("Unable to import %s" % objectName)
            else:                        
                if not isinstance(child, ModuleType):
                    return module, objectNames[i:]
                else:
                    module = child
                
        else:
            module = _importFromModule(name)
      
    return module,[]

def findModule(moduleName, finder=imp.find_module):
    """ Gets the absolute path of a module."""
    
    path = None
    for name in moduleName.split("."):
        y,path,z = finder(name, [path] if path else None)
    return path

def absModuleName(name, base, finder=imp.find_module):
    """ Gets the absolute name of a module that has been imported by `base`."""

    if "." in name:
        name,rest = name.split(".", 1)
    else:
        rest = None
        
    absName, f, path, desc = _findModule(name, base, finder)

    if rest:
        return absName + "." + rest
    else:
        return absName

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def _importFromModule(name, base=None, finder=imp.find_module, loader=imp.load_module):
    if base:
        if not hasattr(base, "__path__"):
            # Before we actually import, get the module's package and see if the name has
            # already been imported and cached there
            baseName = base.__name__
            if "." in baseName:
                baseName,tail = base.__name__.rsplit(".", 1)

            package = importObject(baseName, None, finder, loader)
            child = getattr(package, name, NonExistent)
            if child is not NonExistent:
                return child

        absName, f, path, desc = _findModule(name, base, finder)
        module = loader(absName, f, path, desc)
        
        # Cache the sub-module on its parent module
        setattr(base, name, module)
    else:    
        module = __import__(name)
        
    return module

def _findModule(name, base, finder=imp.find_module):
    packagePath = getPackagePath(base)
    paths = ([packagePath] + sys.path) if os.path.isdir(packagePath) else None
    found = finder(name, paths)
    if not found:
        raise ImportError("Unable to import %s" % name)

    f, path, desc = found
    if os.path.normcase(os.path.dirname(path)) == os.path.normcase(packagePath):
        # The path of the file we found is contained in the same path as the base module,
        # therefore we know that it is a relative import
        absName = getPackageChildName(base, name)
    else:
        absName = name
    
    return absName, f, path, desc

# **************************************************************************************************

def getRootPackagePath(module, finder=imp.find_module, loader=imp.load_module):
    """ Gets the top-level path that contains a module. This path should be in the python path."""
    
    packageName = module.__name__
    if '.' in packageName:
        packageName,tail = module.__name__.split('.', 1)
     
    package = importObject(packageName, finder=finder, loader=loader)
    packagePath, = package.__path__
    return os.path.dirname(packagePath)

def getPackagePath(module):
    if hasattr(module, "__path__"):
        return module.__path__[0]
    else:
        return os.path.dirname(module.__file__)

def getPackageChildName(module, childName):
    baseName = module.__name__

    if childName == "__init__":
        return baseName

    if not hasattr(module, "__path__") and "." in baseName:
        baseName,x = baseName.rsplit(".", 1)

    if baseName:
        return baseName + "." + childName
    else:
        return childName
        
# **************************************************************************************************

def walkModules(moduleName):
    """Iterates each module inside of and including moduleName, importing each as we go."""

    for subModuleName in walkModuleNames(moduleName):
        try:
            yield importModule(subModuleName)
        except GeneratorExit:
            raise
        except:
            print "* Unable to import %s" % subModuleName
            raise

def walkModuleNames(moduleName):
    """ Iterates the names of each module inside of and including moduleName.
        
        This only recognizes modules with the .py extension."""

    ignoreNames = ["project"]
    
    def iter(moduleName, modulePath, isDir):
        if isDir:
            names = os.listdir(modulePath)
            if not "__init__.py" in names:
                return
        else:
            moduleName,baseName = moduleName.rsplit(".", 1)
            names = [baseName+".py"]
        
        for name in names:
            filePath = os.path.join(modulePath, name)
            if os.path.isdir(filePath):
                dirModuleName = ".".join((moduleName, name))
                dirPath = os.path.join(modulePath, name)
                for name in iter(dirModuleName, dirPath, True):
                    yield name
            
            else:
                baseName,ext = os.path.splitext(name)
                if ext == ".py":
                    if baseName == "__init__":
                        yield moduleName
                    elif baseName not in ignoreNames:
                        yield ".".join((moduleName, baseName))
    
    # Find the path of the module and then iterate all of the names in its directory
    modPath = findModule(moduleName)
    if modPath:
        isDir = os.path.isdir(modPath)
        if isDir:
            dirPath = modPath
            modPath = os.path.join(modPath, "__init__.py")
        else:
            dirPath = os.path.dirname(modPath)

        for name in iter(moduleName, dirPath, isDir):
            yield name

# **************************************************************************************************

def getCallerGlobals():
    """Gets the locals dictionary of the calling frame."""

    return getFrameGlobals(2)

def getFrameGlobals(n):
    """Gets the locals dictionary of a frame n levels behind."""
    
    return sys._getframe(n+1).f_globals
