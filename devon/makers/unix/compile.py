
import devon.makers, devon.make, devon.parsers.gcc
from devon.tags import *
import os.path, re, time

reCFiles = re.compile(r"\.(cpp|c|cxx|m|mm)$")

# **************************************************************************************************

class Compile(devon.makers.Compile):
    path = "g++"
    parser = devon.parsers.gcc.GCCParser()
    
    def getSourceTarget(self, project, source):
        if source == project.pch:
            return "%s.gch" % source
            
        elif reCFiles.search(source):
            target = re.sub(r"\.(cpp|c|cxx|m|mm)$", r".o", source)
            return target
    
    def build(self, project, out, source, target):
        args = self.getBaseArgs(project, source, target)
        
        if project.pedantic:
            args += " -pedantic"
        
        if len(source) >= 2 and source[-2:] == ".h":
            args += " -x c++-header"

        line = "%s %s -c -o %s %s" % (self.path, args, target, source)
        #c1 = time.time()
        result = devon.make.executeCommand(project, self, line, out)
        #c2 = time.time()
        #print "built %s in %f" % (source, c2-c1)
        return result
        
    def printAction(self, project, out, source, target):
        out << Block("progressBox progress-build") << "Compiling " \
            << FileLink(basePath=project.path, path=source) << source << Close \
            << "..." << Close << Flush

    def printResult(self, project, out, text):
        if project.formatOutput:
            self.parser.parse(text, project, out)
        else:
            out << CodeBlock << text << Close

    def getBaseArgs(self, project, source, target):
        # The "no-long-double" option seems to be a mac-only thing
        import sys
        if sys.platform == "darwin":
            # Causes error on Snow Leopard
            #args = "-Wno-long-double "
            args = ""
        else:
            args = ""

        if project.compilerFlags:
            args += project.compilerFlags + " "

        args += self.getOptimizeFlag(project)
        
        # XXXjoe Building on the fb sandboxes without this flag causes a link error on some libs
        #args += " -fPIC"
        
        for name in vars(project.defines):
            value = getattr(project.defines, name)
            if value:
                args += ' -D%s=%s' % (name, value)

        args += " -I%s" % project.getBuildPath()
        for includePath in project.getIncludePaths(True, source):
            args += " -I%s" % includePath

        return args

    def getOptimizeFlag(self, project):
        session = devon.projects.getSession()
        vals = {"size": "-Os", "speed": "-O3", "full": "-O3"}
        if session.optimize in vals:
            return vals[session.optimize]
        else:
            return "-g -DDEBUG -D_DEBUG"
    
# **************************************************************************************************

class CompileTestRunner(Compile, devon.makers.CompileTestRunner):
    def filterSources(self, project, sources):
        return devon.makers.CompileTestRunner.filterSources(self, project, sources)