
import os, datetime, re

reGitDateField = re.compile(r"Date:   (.*?) -?\d+$", re.MULTILINE)

def getLatestTimestamp(gitPath):
    """ Gets the timestamp of the last git commit."""
    
    os.chdir(gitPath)
    f = os.popen("%s rev-list HEAD --pretty --max-count=1" % os.environ['TM_GIT'])
    text = f.read()
    
    m = reGitDateField.search(text)
    if m:
        return datetime.datetime.strptime(m.groups()[0], "%a %b %d %H:%M:%S %Y")
