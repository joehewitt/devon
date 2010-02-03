
import devon.maker, devon.make
from devon.tags import *
import re

reLexFiles = re.compile(r"\.(lex)$")
reBisonFiles = re.compile(r"\.(y)$")

# **************************************************************************************************

class FlexParse(devon.maker.Preprocessor):
    def getSourceTarget(self, project, source):
        if reLexFiles.search(source):
            return re.sub(reLexFiles, r".yy.cpp", source)
            
    # XXXblake Investigate issue (likely with make.executeCommand) wherein when flex was not
    # installed on Debian, no error was thrown, and compilation proceeded (only to fail when the
    # flex-output file could not be found); try removing flex and cleaning/building JUL on Debian
    def build(self, project, out, source, target):
        line = "/usr/local/bin/flex -o%s %s" % (target, source)

        result = devon.make.executeCommand(project, self, line, out)
        return result
                
    def printAction(self, project, out, source, target):
        out << Block("progressBox progress-build") << "Parsing " \
            << FileLink(basePath=project.path, path=source) << source << Close \
            << "..." << Close << Flush

    def printResult(self, project, out, text):
        out << CodeBlock << text << Close

class BisonParse(devon.maker.Preprocessor):
    def getSourceTarget(self, project, source):
        if reBisonFiles.search(source):
            return re.sub(reBisonFiles, r".tab.cpp", source)
            
    def build(self, project, out, source, target):
        line = "/usr/local/bin/bison -v -d -o %s %s" % (target, source)

        result = devon.make.executeCommand(project, self, line, out)

        return result
                
    def printAction(self, project, out, source, target):
        import os.path
        fileName,ext = os.path.splitext(os.path.basename(source))
        outputPath = os.path.join(project.getBuildPath(), "%s.output" % fileName)

        out << Block("progressBox progress-build") << "Parsing " \
            << FileLink(basePath=project.path, path=source) << source << Close \
            << "... (" << FileLink(basePath=project.path, path=outputPath) << "summary" << Close  << ")" \
            << Close << Flush

    def printResult(self, project, out, text):
        out << CodeBlock << text << Close
