#! /usr/bin/python

import devon.projects.run
import getopt, sys

# **************************************************************************************************

projectPath = None

opts, args = getopt.getopt(sys.argv[1:], "p:", ["project="])

for name,val in opts:
    if name == "-p" or name == "--project":
        projectPath = val

project = devon.projects.load(projectPath)
if project:
    devon.projects.run.runProjectExecutable(project)
