
import os, signal, sys

# **************************************************************************************************

if sys.platform == "win32":
    import win32process
    os.kill = win32process.TerminateProcess
    
def main(request):
    try:
        pid = int(request.args["pid"])
        os.kill(pid, signal.SIGINT)

        # XXXjoe I should probably only kill the process after waiting for the SIGINT to fail
        #os.kill(pid, signal.SIGKILL)
    except:
        request.wfile.write("0")
        raise
    else:
        request.wfile.write("1")
