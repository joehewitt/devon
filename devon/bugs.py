
import re, sys, os.path, datetime
from devon.rcs import getLatestTimestamp
import devon.projects

reLine = re.compile(r"={3,}")
reHeader = re.compile(r"(.*?)\s*(@\d{2,})?\s*\n(={3,})\n", re.MULTILINE)
reHistoryDateField = re.compile(r"(.*?)\s*(@\d{2,})\s*\<(.*?)\>")

selectedSeparator = "21432142315213521309dsa9hfaspdfsdaio"

# **************************************************************************************************

def parseBugsFromBugFile(text):
    """ Parses the contents of a bug file into a list of bugs."""

    m = reHeader.search(text)
    offset = -1    
    while m:
        offset = m.end()
        title, bug, separator = m.groups()
        bug = bug or ""
        
        m = reHeader.search(text, m.end()+1)
        if m:
            body = "\n%s\n\n" % text[offset:m.start()].strip() 
        else:
            body = ""

        yield (title, bug, separator, body)

# **************************************************************************************************

def getBugsPathForProject(projectPath):
    """ Gets the path of the bug file for a project."""
    try:
        project = devon.projects.load(projectPath)
        if projectPath in project.config.bugFiles:
            return project.config.bugFiles[projectPath]
    except Exception, exc:
        return None

def getBugHistoryPath(bugFilePath):
    """ Gets the path of the bug history file that goes with a bug file."""
    fileName,fileExt = os.path.splitext(bugFilePath)
    return "%s-History%s" % (fileName, fileExt)

def getBugHistory(bugFilePath, mode="r"):
    """ Opens the bug history file that goes with a bug file."""
    if bugFilePath:
        historyPath = getBugHistoryPath(bugFilePath)
        return file(historyPath, mode)

# **************************************************************************************************

def getBugsFixedSinceLastCommit(projectPath):
    """ Gets a list of bugs that have been fixed since the last commit."""
    
    bugsPath = getBugsPathForProject(projectPath)
    if not bugsPath:
        return
        
    commitTime = getLatestTimestamp(projectPath)
    if not commitTime:
        print "%s is not a valid repository"

    doneFile = getBugHistory(bugsPath)
    if not doneFile:
        print "There is no history for %s" % bugsPath
    
    text = doneFile.read()
    for title, bug, separator, body in parseBugsFromBugFile(text):
        m = reHistoryDateField.search(title)
        fixTime = datetime.datetime.strptime(m.groups()[2], "%a %b %d %H:%M:%S %Y")
        if fixTime > commitTime:
            yield (m.groups()[0], m.groups()[1], commitTime)

def getBugsFixedSummary(projectPath):
    """ Generates a summary of bugs fixed in a project since the last commit."""
    
    if not os.path.isdir(projectPath):
        projectPath = os.path.dirname(projectPath)
        if os.path.basename(projectPath) in [".git", ".svn"]:
            projectPath = os.path.dirname(projectPath)

    files = list(getBugsFixedSinceLastCommit(projectPath))
    changes = []
    if files:
        for title, bug, delta in files:
            changes.append("* Fixed bug %s: %s" % (bug, title))
    
    return "\n".join(changes)

def getBugLineNumber(text, bugNumber):
    """ Gets the line number where a bug is defined."""
    
    reBugHeader = re.compile(r".*?\s*@%s\s*\n={3,}\n" % bugNumber, re.MULTILINE)
    m = reBugHeader.search(text)
    if m:
        text = text[0:m.start()]
        return len(text.split("\n"))

# **************************************************************************************************
          
def insertNew(text, lineNumber=0):
    """ Inserts a new bug in a bug file."""
    
    lines = text.split("\n")
    newBugTitle = lines[lineNumber-2]
    del lines[lineNumber-2:lineNumber]

    text = "\n".join(lines)
    for title, bug, separator, body in parseBugsFromBugFile(text):
        if title == "NEW":
            newBugNumber = int(bug[1:])
            bug = "@%s" % (newBugNumber + 1)

            sys.stdout.write("%s @%s\n%s\n\n\n\n" % (newBugTitle, newBugNumber, separator))

        sys.stdout.write("%s %s\n%s\n%s" % (title, bug, separator, body))
            
def markBugFixed(text, path="", lineNumber=0):
    """ Marks a bug fixed by moving it to the bug history file."""
    
    doneFile = getBugHistory(path, "a")
    
    lines = text.split("\n")
    lineNumber += 1
    for i in xrange(0, lineNumber):
        index = lineNumber-i
        line = lines[index]
        if reLine.match(line):
            lines.insert(index+1, selectedSeparator)
            break

    text = "\n".join(lines)

    for title, bug, separator, body in parseBugsFromBugFile(text):
        if body.find(selectedSeparator) != -1:
            if doneFile:
                body = body.replace(selectedSeparator+"\n\n", "")
                timestamp = datetime.datetime.now().ctime()                
                doneFile.write("%s %s <%s>\n%s\n%s" % (title, bug, timestamp, separator, body))
        else:
            sys.stdout.write("%s %s\n%s\n%s" % (title, bug, separator, body))
