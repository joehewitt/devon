#! /usr/bin/python

import devon.projects.jump
import getopt, sys

# **************************************************************************************************

if len(sys.argv) < 2:
    print """usage: jump.py filename... [--text ...] [--offset ...] [--relative ..]"""
    sys.exit()

opts, args = getopt.getopt(sys.argv[2:], "t:o:r:", ["text=", "offset=", "relative="])

sourcePath = sys.argv[1]
sourceText = None
sourceOffset = None
relative = None

for name,val in opts:
    if name == "-t" or name == "--text":
        sourceText = val
    elif name == "-o" or name == "--offset":
        sourceOffset = int(val)
    elif name == "-r" or name == "--relative":
        relative = val

devon.projects.jump.jump(sourcePath, sourceText, sourceOffset, relative)
