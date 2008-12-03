
# **************************************************************************************************

class Maker:
    def __init__(self):
        self.nextMaker = None
        self.previousMaker = None
        
    def __rshift__(self, other):
        self.nextMaker = other
        other.previousMaker = self
        return other

    def filterSources(self, project, sources):
        return sources

    def getDependencies(self, project):
        return []


    def install(self, project, out, sources, target):
        return 0

    def printResult(self, project, out, text):
        pass
        
class MakerOneToOne(Maker):
    def needsUpdate(self, project, source, target):
        return False

    def getSourceTarget(self, project, source):
        return ""
                
    def printAction(self, project, out, source, targets):
        pass

class MakerOneToMany(Maker):
    def needsUpdate(self, project, source, target):
        return False

    def getSourceTargets(self, project, source, target):
        return []
    
    def printAction(self, project, out, source, target):
        pass
        
class MakerManyToOne(Maker):
    def getTarget(self, project):
        return ""
                
    def needsUpdate(self, project, target):
        return False

    def printAction(self, project, out, target):
        pass

class Preprocessor(Maker):
    def needsUpdate(self, project, source, target):
        return False

    def getSourceTarget(self, project, source):
        return ""
                
    def printAction(self, project, out, source, target):
        pass
