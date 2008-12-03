
import devon.wiki
import os.path

# **************************************************************************************************

def main(request):
    request.servePage("wiki.html", globals(), locals())

def renderPage(request):
    if not request.project.wikiPath:
        return request.serve404("Project has no Wiki")
        
    docPath = request.project.getDocumentPath(request.path)
    if not os.path.isfile(docPath):
        return request.serve404("Document '%s' not found" % docPath)

    devon.wiki.renderPage(docPath, request.out)
