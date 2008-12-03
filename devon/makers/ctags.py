
import devon.maker, devon.make
from devon.tags import *

# **************************************************************************************************

class CTags(devon.maker.MakerManyToOne):
    path = "ctags"
    
    def getTarget(self, project):
       return "tags"
    
    def build(self, project, out, sources, target):
        sourceLine = " ".join([source for source in sources])
        
        line = "%s -f %s %s" % (self.path, target, sourceLine)
        
        return devon.make.executeCommand(project, self, line, out)

    def printAction(self, project, out, target):
        out << Block << "Generating " << FileLink(path=target) \
            << "tags" << Close << "..." << Close

    def printResult(self, project, out, text):
        out << Block << text << Block
