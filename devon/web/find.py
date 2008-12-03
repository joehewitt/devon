
import devon.projects, devon.make, devon.search
from devon.tags import *

# **************************************************************************************************

def main(request):
    request.servePage("process.html", globals(), locals())

def process(request):
    fileTypes = None
    if "fileTypes" in request.args:
        fileTypes = request.args["fileTypes"]

    caseSensitive = False
    if "caseSensitive" in request.args:
        caseSensitive = request.args["caseSensitive"]
    
    findCount = 0
    
    if "replaceTerms" in request.args:
        request << Header(level=1) << 'Replacing "%s" with "%s"...' \
            % (request.args["terms"], request.args["replaceTerms"]) \
            << Close << Flush

        project = request.getTargetProject()
        if project:        
            findCount += devon.search.searchProject(project, request.args["terms"],
                request.out, request.args["replaceTerms"], fileTypes, caseSensitive)
    else:
        request << Header(level=1) << 'Searching for "%s"...' % request.args["terms"] \
            << Close << Flush

        project = request.getTargetProject()
        if project:        
            findCount = devon.search.searchProject(project, request.args["terms"],
                request.out, fileTypes=fileTypes, caseSensitive=caseSensitive)

    request << Block("resultBox") << """Found %d matches.""" % findCount << Block
