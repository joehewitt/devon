
import devon.run
import os.path

# **************************************************************************************************

def main(request):
    devon.run.writeProjectCatalog(request.project, request.out)
