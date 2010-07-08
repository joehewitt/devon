
import devon.maker, devon.make
from devon.tags import *
import re, os.path

# **************************************************************************************************

class ConfigureMake(devon.maker.MakerManyToOne):
    def getTarget(self, project):
        return project.config.output
            
    def build(self, project, out, source, target):
        line = "make clean"
        result = devon.make.executeCommand(project, self, line, out)

        if project.config.configure:
            line = project.config.configure
        else:
            line = "./configure"
        result = devon.make.executeCommand(project, self, line, out)
        
        line = "make"
        result = devon.make.executeCommand(project, self, line, out)
        
        line = "cp %s %s" % (self.getTarget(project), target)
        result = devon.make.executeCommand(project, self, line, out)
        return result
                
    def printAction(self, project, out, target):
        out << Block << "Configuring and making " << FileLink(path=target) \
            << target << Close << "..." << Close

    def printResult(self, project, out, text):
        out << CodeBlock << text << Close
