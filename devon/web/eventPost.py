
import devon.web
import os.path, xmlrpclib

# **************************************************************************************************

def main(request):
    params, method = xmlrpclib.loads(request.data)

    devon.web.postUserEvent(method)
    
    response = xmlrpclib.dumps((0,), methodresponse=1)
    request.serveText(response)
