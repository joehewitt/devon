#! /usr/bin/python

import devon.make
import getopt, sys

# **************************************************************************************************

projectPath = None
actions = None

opts, args = getopt.getopt(sys.argv[1:], "p:", ["project="])
if len(sys.argv) > 1:
    actions = sys.argv[1]

for name,val in opts:
    if name == "-p" or name == "--project":
        projectPath = val

# XXXblake Wrappers below are temporary, we need to clean this mess up
import devon.web, devon.projects
devon.web.loadSites()
devon.projects.loadExternalProjects()

if actions:
    for action in actions.split(","):
        devon.make.make(projectPath, action)
else:
    devon.make.make(projectPath)
        
devon.projects.shutdownProjects()
