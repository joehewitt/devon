
import devon.jump
import os.path, sys, glob

# **************************************************************************************************

def main(request):
    if "line" in request.args:
        line = request.args["line"]
    else:
        line = -1

    if "col1" in request.args and "col2" in request.args:
        col1 = request.args["col1"]
        col2 = request.args["col2"]
    else:
        col1 = -1
        col2 = -1
    
    if "basePath" in request.args and request.args["basePath"]:
        project = devon.projects.load(request.args["basePath"])
    else:
        project = request.project
    
    request.send_response(200)
    request.send_header("Content-type", "text/plain")
    request.end_headers()

    if os.path.exists(request.path):
        fullPath = request.path
    else:
        fullPath = devon.jump.expandPath(project, request.path)
        
    if fullPath:
        devon.jump.launchFile(fullPath, line, col1, col2)
        request.wfile.write("1")
    else:
        request.wfile.write("0")
