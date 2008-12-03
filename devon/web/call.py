
import devon.jump, devon.code.sync
import xmlrpclib, sys
   
# **************************************************************************************************

def main(request):
    params, method = xmlrpclib.loads(request.data)

    try:
        fn = eval(method)
    except:
        fn = None
        result = xmlrpclib.Fault(1, "Function '%s' not found" % method)
        response = xmlrpclib.dumps(result)
    
    if fn:
        try:
            result = fn(request, *params)
            if result == None:
                result = ""
            response = xmlrpclib.dumps((result,), methodresponse=1)
        except:
            result = xmlrpclib.Fault(1, "%s:%s" % (sys.exc_type, sys.exc_value))
            response = xmlrpclib.dumps(result)
            raise

    request.send_response(200)
    request.send_header("Content-type", "text/xml")
    request.send_header("Content-length", str(len(response)))
    request.end_headers()
    request.wfile.write(response)

def jump(request, sourcePath, sourceText, sourceOffset, relative):
    jumpPath = devon.jump.jump(sourcePath, sourceText, sourceOffset, relative)
    return jumpPath

def jumpLaunch(request, sourcePath, sourceText, sourceOffset, relative):
    return devon.jump.launch(sourcePath, sourceText, sourceOffset, relative)

def shutdown(request):
    devon.server.web.stopServer()
