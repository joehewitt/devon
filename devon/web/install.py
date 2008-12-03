
import devon.make
from devon.tags import *

# **************************************************************************************************

def main(request):
    request.servePage("process.html", globals(), locals())

def process(request):
    request.out << Header(level=1) << "Installing..." << Close << Flush

    if "config" in request.args:
        config = request.args["config"]
    else:
        config = "debug"

    project = request.getTargetProject()
    result = devon.make.make(project, "install", request.out, config)

    if result == 0:
        request << Block("resultBox result-success") << "Success" << Close
    else:
        request << Block("resultBox result-failure") << "Errors occurred" << Close
