
import devon.maker
from devon.tags import *
import datetime, os.path, shutil

# **************************************************************************************************

class DiskImage(devon.maker.MakerManyToOne):
    path = "hdiutil"
    
    def getTarget(self, project):
        return "%s.dmg" % project.name
        
    def needsUpdate(self, project, target):
        return True
        
    def build(self, project, out, sources, target):
        bytes = 0.0
        for source in sources:
            bytes += getDirectorySize(source)
        
        # Pad the rounding error a little, or we'll run out of space when copying
        megabytes = bytes/1000000 + 0.2
        
        out << Block("progressBox progress-build") << "Creating disk image " \
                << FileLink(path=target) << target << Close << "..." \
            << Close
        
        # Create the disk image
        line = "%s create '%s' -megabytes %f -volname '%s' -fs HFS+" \
            % (self.path, target, megabytes, project.name)

        result = devon.make.executeCommand(project, self, line, out)

        # Mount the disk image
        line = "%s attach '%s'" % (self.path, target)
        result = devon.make.executeCommand(project, self, line, out)

        # Copy each file to the disk image
        volumeName = "/Volumes/%s/" % project.name        
        for source in sources:
            os.system("cp -R '%s' '%s'" % (source, volumeName))
        
        # Unmount the disk image
        line = "%s detach '%s'" % (self.path, volumeName)
        result = devon.make.executeCommand(project, self, line, out)
        

        return result
        
    def printAction(self, project, out, target):
        out << Block("progressBox progress-build") << "Archiving " \
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

def getDirectorySize(path):
    size = 0
    for root, dirs, files in os.walk(path):
        print "%s" % files
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    
    # XXXjoe On OS X at least, the number is double its actual size for some reason
    return size/2
