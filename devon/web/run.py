
import devon.run
from devon.tags import *

# **************************************************************************************************

def main(request):        
    request.servePage("process.html", globals(), locals())

def process(request):
    if "target" in request.args:
        target = request.args["target"]
    else:
        target = None
    
    if "disabledLogs" in request.args:
        disabledLogs = request.args["disabledLogs"].split(",")
    else:
        disabledLogs = None

    if "debugger" in request.args:
        debugger = request.args["debugger"] == "true"
    else:
        debugger = False
    
    if target:
        parts = target.split("/")
        lastPart = "/".join(parts[2:])
        colon = lastPart.find(":")
        if colon != -1:
            prefix = lastPart[:colon]
            targetName = lastPart[colon+1:]
            projectId = devon.run.testIdToPath(parts[0])
            testProject = devon.projects.load(projectId)
            
            if prefix == "exe":
                devon.run.runProjectExecutable(testProject, targetName, disabledLogs,
                    debugger, request.out)
            elif prefix == "py":
                devon.run.runProjectPython(testProject, targetName, disabledLogs,
                    debugger, request.out)
                
                return
            
    devon.run.runProjectTests(request.project, target, disabledLogs, debugger, request.out)
