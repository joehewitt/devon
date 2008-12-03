
from devon.projects import jump

import os.path, re

# **************************************************************************************************
# Constants

reStrings = (
    r'"(.+?)"',
    r"'(.+?)'",
)

rePythonImports = (
    "^\s*import\s*",
    "^\s*from\s*"
)

# **************************************************************************************************

class PythonJumper(jump.Jumper):
    def canHandleFileType(self, ext):
        return ext == "py"
    canHandleFileType = classmethod(canHandleFileType)
    
    def jumpText(self, sourcePath, sourceText, caretOffset):
        sourceDirPath = os.path.dirname(sourcePath)
        
        for target, relist in jump.getPatternMatch(sourceText, [rePythonImports, reStrings]):
            if relist == rePythonImports:
                moduleName = jump.getFocusedSymbol(sourceText, caretOffset, "[\.\w]")
                module = __import__(moduleName)
                if module and hasattr(module, "__file__"):
                    modulePath = module.__file__
                    if modulePath[-3:] == "pyc":
                        modulePath =  modulePath[:-1]
                    
                    return modulePath
                
                break
                
            elif relist == reStrings:
                return jump.expandIncludedPath(self.project, sourceDirPath, target)
