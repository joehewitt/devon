import devon.maker
import os.path, time
from devon import tags

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# Compile behaviors common to all platforms.

class Compile(devon.maker.MakerOneToOne):
    def needsUpdate(self, project, source, target):
        """ Returns true if the specified source file needs to be rebuilt, or
            false otherwise.
        """
        if source in project.alwaysBuild:
            return True

        # A source file needs to be rebuilt if any header file it includes directly or indirectly,
        # has changed.
        # XXXblake This would probably be faster if we kept a map of all headers in all
        # projects and the sources that include them, then ran through that.
        targetMod = os.path.getmtime(target)
        for header in project.getSourceDependencies(source, deep=True):
            # Skip targetNeedsUpdate here since we want this to be fast, and
            # that checks for path existence and retrieves target mod time
            # each call.
            if os.path.getmtime(header) > targetMod:
                return True
        return False

class CompileTestRunner(Compile):
    def filterSources(self, project, sources):
        import devon
        
        session = devon.projects.getSession()
        if not project.debug:
            return []

        sources += project.getTestSources()
        for source in project.testExcludes:
            sources.remove(source)
        return sources

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# Link behaviors common to all platforms.

class Link(devon.maker.MakerManyToOne):
    def printAction(self, project, out, target):
        out << tags.Block("progressBox progress-build") << "Linking " \
            << tags.FileLink(basePath=project.path, path=target) << target << tags.Close \
            << "..." << tags.Close << tags.Flush

    def printResult(self, project, out, text):
        if text:
            out << tags.CodeBlock << text << tags.Close << tags.Flush

class LinkExecutable(Link):
    def getDependencies(self, project):
        return project.getDependencies(deep=True)

class LinkDynamicLib(Link):
    def getDependencies(self, project):
        return project.getDependencies(deep=True)

class LinkStaticLib(Link):
    pass

class LinkTestRunner(LinkExecutable):
    def getTarget(self, project):
        if project.debug:
            return "%s_tests" % project.name
        
    def getDependencies(self, project):
        for dep in LinkExecutable.getDependencies(self, project):
            yield dep
        for dep in LinkTestRunner.__getDeps():
            yield dep
        
    @staticmethod
    def __getDeps():
        if not LinkTestRunner.__deps:
            import devon.projects
            for lib in "testboot", "testenv":
                project = devon.projects.load("%s/%s" % (devon.srcPath, lib))
                LinkTestRunner.__deps.append(project)
        
        return LinkTestRunner.__deps
    __deps = []