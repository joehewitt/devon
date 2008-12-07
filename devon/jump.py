
import devon.projects
import os.path, re, sys

# **************************************************************************************************
# Constants

defaultJumpers = (
    "devon.jumpers.c.CJumper",
    "devon.jumpers.python.PythonJumper"
)

jumperRegistry = []

if sys.platform == "darwin":
    systemIncludePaths = [
        "/usr/include",
        "/usr/local/include",
        "/usr/include/gcc/darwin/default",
        "/usr/include/gcc/darwin/default/c++"
    ]
    
else:
    systemIncludePaths = []
    includePaths = os.environ.get("INCLUDE")
    if includePaths:
        systemIncludePaths += includePaths.split(";")

# **************************************************************************************************

class Jumper:
    def __init__(self, project):
        self.project = project

    def jumpRelative(self, sourcePath, relative):
        if relative == "project":
            return devon.projects.getNearestProjectPath(sourcePath)

    def jumpText(self, sourcePath, sourceText, caretOffset):
        pass
            
    def launch(self, path, line=-1, col1=-1, col2=-1):
        launchFile(path, line, col1, col2)
    
# **************************************************************************************************

def jump(sourcePath, sourceText=None, caretOffset=0, relative=None, project=None, jumper=None):
    if not jumper:    
        jumper = getJumper(sourcePath, project)    

    if jumper:
        if relative:
            return jumper.jumpRelative(sourcePath, relative)
    
        elif sourceText:
            return jumper.jumpText(sourcePath, sourceText, caretOffset)
     
def launch(sourcePath, sourceText=None, caretOffset=0, relative=None, project=None, jumper=None):
    if not jumper:    
        jumper = getJumper(sourcePath, project)    
        
    jumpPath = jump(sourcePath, sourceText, caretOffset, relative, project, jumper)
    if jumpPath:
        jumper.launch(jumpPath)
        return jumpPath
    
def launchFile(path, line=-1, col1=-1, col2=-1):
    if sys.platform == "darwin":
        cleanPath = os.path.abspath(path)

        if os.path.isdir(cleanPath):
            os.system("open %s" % cleanPath)

        elif os.path.isfile(cleanPath):
            if line >= 0:
                os.system('mate -l %s "%s"' %  (line, cleanPath))
            else:
                os.system('mate "%s"' % cleanPath)
    
    elif sys.platform == "win32":
        cleanPath = os.path.abspath(path)

        if os.path.isdir(cleanPath):
            os.system("explorer %s" % cleanPath)

        elif os.path.isfile(cleanPath):
            scriptPath = "editMSVC.py"
            command = '%s "%s" %s %s %s' % (scriptPath, cleanPath, line, col1, col2)
            os.system(command)

def expandPath(project, sourcePath):
    fullPath = expandProjectPath(project, sourcePath)
    if not fullPath:
        fullPath = expandIncludedPath(project, project.path, sourcePath)
    
    return fullPath

# **************************************************************************************************

def getJumper(sourcePath, project=None):
    if not project:
        project = devon.projects.load(sourcePath)

    if not len(jumperRegistry):
        for className in defaultJumpers:
            jumperClass = importSymbol(className)
            if jumperClass:
                jumperRegistry.append(jumperClass)
            
    ext = os.path.splitext(sourcePath)[1][1:]
    for jumperClass in jumperRegistry:
        if jumperClass.canHandleFileType(ext):
            return jumperClass(project)

def getPatternMatch(sourceText, patternLists):
    """Search for a pattern in a list that matches the given text"""
    
    for patternList in patternLists:
        for pattern in patternList:
            reg = re.compile(pattern)
            m = reg.search(sourceText)
            if m:
                if len(m.groups()):
                    yield m.groups()[0], patternList
                else:
                    yield sourceText, patternList

def getFocusedSymbol(sourceText, caretOffset, symbolChars="[\w]"):
    startOffset = 0
    endOffset = 0
    reChar = re.compile(symbolChars)
    
    n = caretOffset-1
    while n > 0:
        if not reChar.match(sourceText[n]):
            break
        n -= 1

    startOffset = n+1
    
    n = caretOffset
    while n < len(sourceText):
        if not reChar.match(sourceText[n]):
            break
        n += 1

    endOffset = n
    
    return sourceText[startOffset:endOffset]    

def expandProjectPath(project, fileName):
    paths = project.getSources() \
        + project.getPathList(project.debugSources) \
        + project.getTestSources()

    minIndex = 4294967295
    foundPath = None
    for source in paths:
        sourcePath = os.path.join(project.path, source)
        index = sourcePath.find(fileName)
        if index >= 0 and index < minIndex:
            minIndex = index
            foundPath = sourcePath
    
    if foundPath:
        return foundPath
            
    for child in project.getChildProjects():
        fullPath = expandProjectPath(child, fileName)
        if fullPath:
            return fullPath
        
def expandIncludedPath(project, sourceDirPath, path):
    testPath = os.path.join(sourceDirPath, path)
    if os.path.exists(testPath):
        return testPath
    
    # First, Search the root path of the project
    testPath = searchPath(project, path, ["."])
    if testPath:
        return testPath

    # Second, search each of the project include paths
    testPath = searchPath(project, path, project.getIncludePaths(True))
    if testPath:
        return testPath

    # Finally, search each of the system include paths
    testPath = searchPath(project, path, systemIncludePaths)
    if testPath:
        return testPath

    return None

def searchPath(project, path, paths):
    """Search for a path in a list of paths that are relative to the project path"""
    
    for dir in paths:
        testPath = os.path.join(project.path, dir)
        if os.path.exists(testPath):
            testFilePath = os.path.join(testPath, path)
            if os.path.exists(testFilePath):
                return testFilePath
    
    return None
    
def recurseProjectPaths(project, sourcePath, targetName):
    """Recursively search directories within a project for a file by name"""
    
    testPath = os.path.join(sourcePath, targetName)
    if os.path.exists(testPath):
        return testPath
    
    def searchDir(sourcePath, targetName):
        testPath = os.path.join(sourcePath, targetName)
        if os.path.exists(testPath):
            return testPath
            
        dirNames = os.listdir(sourcePath)
        for dirName in dirNames:
            dirPath = os.path.join(sourcePath, dirName)
            if os.path.isdir(dirPath):
                found = searchDir(dirPath, targetName)
                if found:
                    return found
    
    if project:
        return searchDir(project.path, targetName)    
    
def expandRelativePath(project, path):
    testPath = os.path.abspath(os.path.join(project.path, path))
    if os.path.exists(testPath):
        return testPath
    else:
        return None

def importSymbol(moduleName):
    names = moduleName.split(".")
    moduleName = ".".join(names[0:-1])

    symbol = __import__(moduleName)
    for name in names[1:-1]:
        symbol = getattr(symbol, name)

    reload(symbol)
    return getattr(symbol, names[-1])
            