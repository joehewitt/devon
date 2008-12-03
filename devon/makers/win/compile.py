
import devon.maker, devon.makers.win.link, devon.make, devon.parsers.msvc
from devon.tags import *
import os.path, re

# **************************************************************************************************
# Constants

reCFiles = re.compile(r"\.(cpp|c|cxx)$")
reIDLFiles = re.compile(r"\.(idl)$")
reRCFiles = re.compile(r"\.(rc)$")

# **************************************************************************************************

class Compile(devon.makers.Compile):
    path = "cl"
    parser = devon.parsers.msvc.CLParser()
    
    def getSourceTarget(self, project, source):
        if reCFiles.search(source):
            if project.pch and source == project.pch.replace(".h", ".cpp"):
                target = source.replace(".h", ".pch")
            else:
                target = re.sub(r"\.(cpp|c|cxx)$", r".o", source)
            return target
    
    def getBaseArgs(self, project, source, target):
        return project.compilerFlags
             
    def build(self, project, out, source, target):    
        args = self.getBaseArgs(project, source, target)

        args += " " + self.getRuntimeFlag(project)
        args += " " + self.getOptimizeFlag(project)
        
        if project.optimize == "debug":
            args += " /RTC1 /ZI"
        
        if project.warningLevel in xrange(0,5):
            args += " /W%d" % project.warningLevel
        
        # XXXblake This adds things like __module__, too    
        for name in vars(project.defines):
            val = getattr(project.defines, name)
            if val:
                args += " /D%s=%s" % (name, val)
        
        # Add in a special define to indicate the user
        args += ' /D "USER_%s"' % project.userName
         
        # XXXblake Don't quite understand the difference between getSourceDependencies (which figures
        # out exactly what a source's header *path* dependencies are) and getDependencies(source) (which
        # returns all the *possible* dependent *projects* for a given source). The former is used to
        # to determine if the file needs rebuilding, while the latter is used below, but why don't
        # we just use the former in both cases (or its algorithm, at least)?
        for includePath in project.getIncludePaths(True, source):
            args += " /I\"%s\"" % includePath

        # If the project has a precompiled header and we're not building a generated file (i.e. a
        # file that lives in the build directory, such as something output by Flex), use the pch
        if project.pch and not source.find(project.getBuildPath()) == 0:               
            if source == project.pch.replace(".h", ".cpp"):  
                args += " /Yc"
            else:
                args += (" /Yu%s" % project.pch)

        command = """%s /c %s /Fo"%s" %s""" % (self.path, source, target, args)
        return devon.make.executeCommand(project, self, command, out)

    def printAction(self, project, out, source, target):
        out << Block("progressBox progress-build") << "Compiling " \
            << FileLink(basePath=project.path, path=source) << source << Close \
            << "..." << Close << Flush

    def printResult(self, project, out, text):
        if project.formatOutput:
            self.parser.parse(text, project, out)
        else:
            out << CodeBlock << text << Close
    
    def getRuntimeFlag(self, project):
        if project.runtimeThreaded:
            # if project.optimize == "debug":
            #     return "/MTd"
            # else:
            #     return "/MT"
             
            # The options below tell the compiler to dynamically link to
            # the runtime libraries. Since most people should have the
            # libraries already, we use these options to reduce the build size,
            # but must be prepared to download these DLLs for people who don't
            # have them.
            if project.optimize == "debug":
               flag = "/MDd"
            else:
               flag = "/MD"
        else:
            if project.optimize == "debug":
                flag = "/MLd"
            else:
                flag = "/ML"

        if isinstance(project.build, devon.makers.win.link.LinkDynamicLib):
            if project.optimize == "debug":
                flag += " /LDd"
            else:
                flag += " /LD"
                
        return flag
                
    def getOptimizeFlag(self, project):
        session = devon.projects.getSession()
        vals = {"size": "/O1", "speed": "/O2", "full": "/Ox"}
        if session.optimize in vals:
            return vals[session.optimize]
        else:
            return '/Od /D_DEBUG'

# **************************************************************************************************
# Resources

class CompileResources(devon.maker.MakerOneToOne):
    path = "rc"
    
    def getSourceTarget(self, project, source):
        if (reRCFiles.search(source)):
            return self.getResourceName(project, source)
    
    def build(self, project, out, source, target):
        args = " /fo %s" % self.getResourceName(project, source)
        command = """%s %s %s""" % (self.path, args, source)
        
        # XXXblake Need to report output properly
        return devon.make.executeCommand(project, self, command, out)
 
    def getBase(self, source):
        dot = source.find(".")
        return source[:dot]
        
    def getResourceName(self, project, source):
        # XXXblake Should be output to build dir, but then we need to deal with libpath
        return self.getBase(source) + ".res"
      
# **************************************************************************************************
# COM Support

class CompileTypeLibraries(devon.maker.MakerOneToOne):
    path = "midl"
    useBuildDirectory = False
    
    def getSourceTarget(self, project, source):
        if (reIDLFiles.search(source)):
            return self.getTypeLibName(source)
    
    def build(self, project, out, source, target):
        args = project.interfaceFlags
        
        args += " /tlb %s" % self.getTypeLibName(source)
        command = """%s %s %s""" % (self.path, args, source)
        return devon.make.executeCommand(project, self, command, out)
 
    def getBase(self, source):
        dot = source.find(".")
        return source[:dot]
        
    def getTypeLibName(self, source):
        return self.getBase(source) + ".tlb"
        
class CompileInterfaces(devon.maker.MakerOneToMany):
    path = "midl"
      
    def getSourceTargets(self, project, source):
        targets = []
        
        if (reIDLFiles.search(source)):
            # Header
            targets.append(self.getHeaderPath(project, source))
        
            # IID
            targets.append(self.getIIDPath(project, source))
            
            # DLL Data
            targets.append(self.getDllDataPath(project, source))
            
            # Proxy
            targets.append(self.getProxyPath(project, source))
        
        return targets
    
    def build(self, project, out, source, target):
        args = project.interfaceFlags

        args += " /proxy %s" % (self.getProxyPath(project, source))
        args += " /h %s" % (self.getHeaderPath(project, source))
        args += " /iid %s" % (self.getIIDPath(project, source))
        args += " /dlldata %s" % (self.getDllDataPath(project, source))
        args += " /tlb %s" % (self.getTlbPath(project, source))
        
        command = """%s %s %s""" % (self.path, args, source)
        return devon.make.executeCommand(project, self, command, out)

    def printAction(self, project, out, source, target):
        out << Block("progressBox progress-build") << "Compiling Interface " \
            << FileLink(basePath=project.path, path=source) << source << Close \
            << "..." << Close << Flush

    def getBase(self, source):
        dot = source.find(".")
        return source[:dot]
        
    def getIIDPath(self, project, source):
        return project.getBuildPath(self.getBase(source) + "_iid.c")
    
    def getHeaderPath(self, project, source):
        return project.getBuildPath(self.getBase(source) + ".h")
        
    def getDllDataPath(self, project, source):
        return project.getBuildPath(self.getBase(source) + "_dll" + ".c")
        
    def getProxyPath(self, project, source):
        return project.getBuildPath(self.getBase(source) + "_proxy" + ".c")
        
    def getTlbPath(self, project, source):
        return project.getBuildPath(self.getBase(source) + ".tlb")
   
# **************************************************************************************************

class CompileTestRunner(Compile, devon.makers.CompileTestRunner):

    def filterSources(self, project, sources):
        return devon.makers.CompileTestRunner.filterSources(self, project, sources)