
import devon.maker
from devon.tags import *
import datetime, os.path, shutil

# **************************************************************************************************

class AppBundle(devon.maker.MakerManyToOne):
    def getTarget(self, project):
        return "%s.app" % project.name
        
    def needsUpdate(self, project, target):
        return True
        
    def build(self, project, out, sources, target):
        bundleContentsPath = os.path.join(target, "Contents")
        bundleOSPath = os.path.join(bundleContentsPath, "MacOS")
        bundleResourcePath = os.path.join(bundleContentsPath, "Resources")

        self.__createDirectories(bundleOSPath)
        self.__createDirectories(bundleResourcePath)
        self.__createFiles(project, target)
        
        osFiles = project.getPathList(project.osFiles)
        resourceFiles = project.getPathList(project.resourceFiles)
        
        print project.expandString(project.executableFile)
        print bundleOSPath
        if project.executableFile:
            self.__copyFile(project.expandString(project.executableFile), bundleOSPath)

        if project.plistFile:
            self.__copyFile(project.expandString(project.plistFile), bundleContentsPath)

        if project.iconFile:
            self.__copyFile(project.expandString(project.iconFile), bundleResourcePath)

        for source in osFiles:
            self.__copyFile(source, bundleOSPath)

        for source in resourceFiles:
            self.__copyFile(source, bundleResourcePath)
        
        return 0
        
    def printAction(self, project, out, target):
        out << Block("progressBox progress-build") << "Bundling " \
                << FileLink(path=target) << target << Close << "..." \
            << Close

    def printResult(self, project, out, text):
        out << Block << text << Close

    def __copyFile(self, source, destDir):
        if os.path.isdir(source):
            newDest = os.path.join(destDir, os.path.basename(source))
            if not os.path.exists(newDest):
                os.makedirs(newDest)

            paths = os.listdir(source)
            for fileName in [name for name in paths if not name[0] == "."]:
                fileSource = os.path.join(source, fileName)
                self.__copyFile(fileSource, newDest)
        else:
            destPath = os.path.join(destDir, os.path.basename(source))
            if os.path.exists(destPath):
                sourceTime = datetime.datetime.fromtimestamp(os.stat(source).st_mtime)
                destTime = datetime.datetime.fromtimestamp(os.stat(destPath).st_mtime)
                if sourceTime > destTime:
                    shutil.copy2(source, destDir)
            else:                    
                shutil.copy2(source, destDir)
        
    def __createDirectories(self, dirName):
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        
    def __createFiles(self, project, target):
        pkginfoPath = os.path.join(target, "Contents", "Pkginfo")
        if not os.path.exists(pkginfoPath) or self.__newerThanProject(pkginfoPath, project):
            f = file(pkginfoPath, "w")
            f.write(project.signature)
            f.close()

    def __newerThanProject(self, sourcePath, project):
        projectPath = os.path.join(devon.projectsFileName, project.path)
        projectTime = datetime.datetime.fromtimestamp(os.stat(projectPath).st_mtime)
        sourceTime = datetime.datetime.fromtimestamp(os.stat(sourcePath).st_mtime)
        return sourceTime > projectTime
        