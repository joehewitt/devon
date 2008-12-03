
import devon.run
import os.path

# **************************************************************************************************

def main(request):
    devon.run.writeProjectTestCatalog(request.project, request.out)
