
import devon.projects
import devon.maker

import sys
import link

from devon.tags import *

import distutils.core, os.path, sys, site, shutil

# **************************************************************************************************

class PythonModules(devon.maker.MakerOneToOne):
    def getSourceTarget(self, project, source):
        return None
        
    def install(self, project, out, source, target):
        
        # Install from top-level directories only
        if not source.find("/") == -1 or not os.path.isdir(source):
            return 0
            
        print "******* installing python"
        oldArgv = sys.argv
        sys.argv = ["", "install"]
        
        def buildSources(sourcePath, packageName, sources=[]):
            sources.append(packageName)

            dirs = os.listdir(sourcePath)
            for dirName in dirs:
                fullPath = os.path.join(sourcePath, dirName)
                if not dirName[0] == "." and os.path.isdir(fullPath):
                    newPackageName = ".".join((packageName, dirName))
                    buildSources(fullPath, newPackageName, sources)
            return sources
            
        out << Block("progressBox progress-install") \
            << "Installing Python module %s..." % source << Close << Flush

        sources = buildSources(source, os.path.basename(source))
        
        try:
            distutils.core.setup(package_dir = { "": "."}, packages = sources)
        except:
            sys.argv = oldArgv
            return 1
        else:            
            sys.argv = oldArgv
            return 0
        
    def printAction(self, project, out, source, target):
        out << Block("progressBox progress-install") \
            << "Installing Python module %s..." % source << Close << Flush

    def printResult(self, project, out, text):
        out << Block("log") << text << Close

class LinkPythonModule(link.LinkDynamicLib):
    def install(self, project, out, source, target):
        if sys.platform == "win32":
            pyDirPath = os.path.join(sys.prefix, 'lib', 'site-packages')
        else:
            # This used to be the place where site-packages was before Leopard
            # pyDirPath = os.path.join(sys.prefix, 'lib', \
            #                          'python' + sys.version[:3], 'site-packages')

            # As of Leopard, they are now stored here
            pyDirPath = os.path.join('/Library/Python', sys.version[:3], 'site-packages')


        targetPath = project.getBuildTarget()
        newTargetPath = os.path.join(pyDirPath, os.path.basename(targetPath))

        out << Block("progressBox progress-install") \
                << "Installing Python module %s..." % os.path.basename(targetPath) \
            << Close << Flush

        shutil.copy2(targetPath, newTargetPath)
        
        return 0
        
# On Windows, the debug version of the Python library only loads extensions if they
# have a _d suffix.
    if sys.platform == "win32":
        def getTarget(self, project):
            if project.debug:
                suffix = "_d"
            else:
                suffix = ""
            
            return "%s%s.pyd" % (project.name, suffix)
