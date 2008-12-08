
import os.path
from devon.rcs import git
from devon.rcs import svn

def getLatestTimestamp(projectPath):
    return getRCSModule(projectPath).getLatestTimestamp(projectPath)

def getRCSModule(projectPath):
    if os.path.isdir(os.path.join(projectPath, ".git")):
        return git
    elif os.path.isdir(os.path.join(projectPath, ".svn")):
        return svn
    