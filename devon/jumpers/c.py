
from devon.projects import jump

import os.path, re

# **************************************************************************************************
# Constants

reStrings = (
    r'"(.+?)"',
    r"'(.+?)'",
)

reCIncludes = (
    r"#include\s*\<(.+?)\>",
    r'#include\s*"(.+?)"',
)

reFileNameCandidate = re.compile(r"[a-zA-Z_][a-zA-Z_\d]*")

# **************************************************************************************************

class CJumper(jump.Jumper):
    def canHandleFileType(self, ext):
        return ext in ("c", "cpp", "h", "hpp")
    canHandleFileType = classmethod(canHandleFileType)
        
    def jumpRelative(self, sourcePath, relative):
        if relative == "up":
            return self.getJumpRelativeUp(sourcePath)
        else:
            return jump.Jumper.jumpRelative(self, sourcePath, relative)

    def jumpText(self, sourcePath, sourceText, caretOffset):
        sourceDirPath = os.path.dirname(sourcePath)
    
        # Check if the text is a C #include and try to lookup the full path of the file
        for (target, relist) in jump.getPatternMatch(sourceText, [reCIncludes, reStrings]):
            fullPath = jump.expandIncludedPath(self.project, sourceDirPath, target)
            if fullPath:
                return fullPath
    
        # Check if the text is a substring of any source file in the project
        if reFileNameCandidate.match(sourceText):
            fullPath = jump.expandProjectPath(self.project, sourceText)
            if fullPath:
                return fullPath

    # **********************************************************************************************

    def getJumpRelativeUp(self, sourcePath):
        implExts = (".cpp", ".c")
        headExts = (".h", ".hpp")
    
        sourceDirPath = os.path.dirname(sourcePath)
        sourceName, sourceExt = os.path.splitext(sourcePath)
        
        candidateExts = None
        if sourceExt in implExts:
            candidateExts = headExts
        elif sourceExt in headExts:
            candidateExts = implExts
        
        if candidateExts:
            sourceFileName = os.path.basename(sourceName)
            for ext in candidateExts:
                targetPath = "%s%s" % (sourceFileName, ext)
                fullPath = jump.recurseProjectPaths(self.project, sourceDirPath, targetPath)
                if fullPath:
                    return fullPath
