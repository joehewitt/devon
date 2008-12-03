
from devon.tags import *
import devon.make

# **************************************************************************************************

def main(request):
    request.servePage("process.html", globals(), locals())

def process(request):
    request.out << Header(level=1) << "Cleaning..." << Close << Flush

    if "config" in request.args:
        config = request.args["config"]
    else:
        config = "debug"

    project = request.getTargetProject()
    result = devon.make.make(project, "clean", request.out, config)

    if result == 0:
        request << Block("resultBox result-success") << "Success" << Close
    else:
        request << Block("resultBox result-failure") << "Errors occurred" << Close
