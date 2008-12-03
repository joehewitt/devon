
import devon.projects.run
import os.path

# **************************************************************************************************

def main(request):
    devon.projects.run.writeProjectLogCatalog(request.project, request.out)
