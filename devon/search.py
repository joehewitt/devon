
import devon, devon.projects
from devon.tags import *
import fnmatch, glob, mmap, os.path, re, sys

reNewLine = re.compile("\n")

# **************************************************************************************************

def search(path, terms, out, replaceTerms=None, fileTypes=None, caseSensitive=True):
    if not terms:
        return 0

    return searchDir(path, terms, replaceTerms, out, fileTypes, caseSensitive)

def searchProject(project, terms, out, replaceTerms=None, fileTypes=None, caseSensitive=True):
    if not terms:
        return 0
    
    projectFilePath = os.path.join(project.path, devon.projects.projectFileName)
    
    paths = [projectFilePath] \
        + project.getSources() \
        + project.getTestSources()

    if fileTypes:
        patterns = fileTypes.split(",")
        def fileFilter(path, patterns):
            for pattern in patterns:
                if fnmatch.fnmatch(path, pattern.strip()):
                    return True
            return False
        paths = [path for path in paths if fileFilter(path, patterns)]

    findCount = 0

    for filePath in paths:
        fullPath = os.path.join(project.path, filePath)
        if os.path.isfile(fullPath) and isSearchable(fullPath):
            findCount += searchFile(fullPath, terms, replaceTerms, out, caseSensitive)
    
    for childProject in project.getChildProjects():
        findCount += searchProject(childProject, terms, out, \
            replaceTerms, fileTypes, caseSensitive)

    return findCount
    
def searchDir(path, terms, replaceTerms, out, fileTypes):
    findCount = 0
    
    if fileTypes:
        dirNames = glob.glob(os.path.join(path, fileTypes))
    else:
        dirNames = os.listdir(path)

    for dirName in dirNames:
        if not dirName[0] == ".":
            dirPath = os.path.join(path, dirName)
            if os.path.isdir(dirPath):
                findCount += searchDir(dirPath, terms, out)
            else:
                findCount += searchFile(dirPath, terms, out)

    return findCount
    
def searchFile(path, terms, replaceTerms, out, caseSensitive):
    findCount = 0
    
    reFlags = 0
    if not caseSensitive:
        reFlags |= re.IGNORECASE

    reTerms = re.compile(re.escape(terms), reFlags)

    if not replaceTerms == None:
        fd = os.open(path, os.O_RDWR)
        size = os.fstat(fd).st_size
        if size == 0:
            os.close(fd)
            return 0
        else:
            source = mmap.mmap(fd, size, access=mmap.ACCESS_WRITE)
            newSource, count = re.subn(reTerms, replaceTerms, source)
            source.close()
            
            if count == 0:
                os.close(fd)
                return 0       
            else:
                os.lseek(fd, 0, 0)
                os.ftruncate(fd, len(newSource))
                os.write(fd, newSource)
                os.close(fd)
                return count

    fd = os.open(path, os.O_RDONLY)
    size = os.fstat(fd).st_size
    if size == 0:
        os.close(fd)
        return 0
    else:    
        source = mmap.mmap(fd, size, access=mmap.ACCESS_READ)
        
        termsLen = len(terms)
        index = 0
        while 1:
            m = reTerms.search(source, index)
            if not m:
                break
            
            findCount += 1
            index = m.start()
            
            lineCount, lineBegin, lineEnd = countLines(source, index)
            snippet = source[lineBegin:lineEnd]
            col1 = m.start()-lineBegin+1
            col2 = m.end()-lineBegin+1
            
            out << Header(level=2) \
                    << FileLink(path=path, lineNo=lineCount, colNo1=col1, \
                                colNo2=col2, rowType="primary") \
                        << "%s (line %s)" % (path, lineCount) \
                    << Close \
                << Close \
                << CodeBlock("log log-snippet") << snippet << Close << Flush

            index += termsLen

        source.close()
        os.close(fd)

    return findCount
    
def countLines(source, endPos):
    lines = 0
    lineBegin = 0
    lineEnd = 0
    
    index = 0
    while index <= endPos:
        m = reNewLine.search(source, index)
        if not m:
            break
        else:
            index = m.end()
            lines += 1
            lineBegin = lineEnd
            lineEnd = index
    
    return lines, lineBegin, lineEnd
    
def isSearchable(path):
    name, ext = os.path.splitext(path)
    name = os.path.basename(name)
    return (not name == "pch.h") and not ext in [".jpg", ".jpeg", ".png", ".gif", ".psd", ".pyc", ".jssc"]
    