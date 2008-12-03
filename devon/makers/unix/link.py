
import devon.makers, devon.make
import os.path, sys

# **************************************************************************************************
# Constants

defaultLibs = ["stdc++"]

# **************************************************************************************************

class Link(devon.makers.Link):
    path = "g++"
    
    def build(self, project, out, sources, target):
        if os.path.basename(target) in project.neverLink:
            return 0

        # Object files must appear before libraries on the link line (see http://tinyurl.com/s97do)
        args = self.getSourceArgs(project, sources, target)
        args += " " + self.getBaseArgs(project, sources, target)            

        line = "%s %s" % (self.path, args)
        return devon.make.executeCommand(project, self, line, out)

    def getSourceArgs(self, project, sources, target):
        def isPrecompiledHeader(source):
            return len(source) >= 4 and source[-4:] == ".gch"
            
        return " ".join([source for source in sources if not isPrecompiledHeader(source)])

    def getBaseArgs(self, project, sources, target):
        args = "-o %s" % target
        
        # Add compiler-specific link flags
        if project.linkerFlags:
            args += " " + project.linkerFlags

        libs = project.getLibs(deep=True, absPaths=True)

        # XXXblake On Linux, link order matters, so our stripping of duplicates in getDependencies()
        # busts the link. Allowing duplicates while still preventing recursion is tricky, however...
        # for example, right now, the Suade serialize and memory projects depend on each other. For
        # now, we use the "grouping" option to force the linker to keep checking the archives until
        # all references are resolved. This has a significant performance cost, as the docs note.
        if not sys.platform == "darwin":
            args += " -Xlinker --start-group"

        # XXXjoe On Mac, link order matters also, but we don't have the luxury of --start-group,
        # so the only hack I can think of is to list libraries twice
        if sys.platform == "darwin":
            libs *= 2

        for libName in libs:
            args += " %s" % libName

        if not sys.platform == "darwin":
            args += " -Xlinker --end-group"
            
        for libName in defaultLibs:
            args += " -l%s" % libName

        for name in project.getFrameworks(True):
            args += " -framework %s" % name
        
        # Ensure that we use the NPTL version of libc on Unix (see http://tinyurl.com/rv49a)
        #if not sys.platform == "win32" and not sys.platform == "darwin":
        #    args += " -L/usr/lib/nptl"
            
        return args

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
        
class LinkExecutable(Link, devon.makers.LinkExecutable):
    def getTarget(self, project):
        return "%s" % project.name
    def getDependencies(self, project):
        return devon.makers.LinkExecutable.getDependencies(self, project)
    
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class LinkStaticLib(Link, devon.makers.LinkStaticLib):
    path = "libtool"
    
    def getTarget(self, project):
        return "lib%s.a" % project.name
        
    def getBaseArgs(self, project, sources, target):
        if not sys.platform == "darwin":
            return "--mode=link g++ -static -o %s" % target
        else:
            return "-static -o %s" % target

    # We need to override Link's build() method so we can format the arg string in the proper order,
    # i.e. we need the base args to come before the source args here
    def build(self, project, out, sources, target):
        if os.path.basename(target) in project.neverLink:
            return 0
        
        line1 = "ar cru %s" % target
        line1 += " " + self.getSourceArgs(project, sources, target)
        devon.make.executeCommand(project, self, line1, out)

        line2 = "ranlib %s" % target
        devon.make.executeCommand(project, self, line2, out)
        #args = self.getBaseArgs(project, sources, target)            
        #args += " " + self.getSourceArgs(project, sources, target)
        
        #line = "%s %s" % (self.path, args)
        #return devon.make.executeCommand(project, self, line, out)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
        
class LinkDynamicLib(Link, devon.makers.LinkDynamicLib):
    def getTarget(self, project):
        return "%s.so" % project.name

    def getBaseArgs(self, project, sources, target):
        args = Link.getBaseArgs(self, project, sources, target)
        
        if sys.platform == "darwin":
            args += " -bundle"
        else:
            args += " -shared"
            
        return args

    def getDependencies(self, project):
        return devon.makers.LinkDynamicLib.getDependencies(self, project)
        
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class LinkTestRunner(LinkExecutable, devon.makers.LinkTestRunner):    
    def getBaseArgs(self, project, sources, target):
        args = LinkExecutable.getBaseArgs(self, project, sources, target)

        # Link in the boot libraries so main() and TestEnvironment are available
        for dep in devon.makers.LinkTestRunner.__getDeps():
            args += " %s" % dep.getBuildTarget()

        return args
        
    def getDependencies(self, project):
        return devon.makers.LinkTestRunner.getDependencies(self, project)
