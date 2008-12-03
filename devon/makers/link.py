import sys

if sys.platform == "win32":
    from devon.makers.win.link import *
else:
    from devon.makers.unix.link import *