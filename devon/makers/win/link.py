
import devon.maker, devon.make, devon.makers
import os.path, sys
from devon import tags

kMtPath = "mt"
defaultLibs = "kernel32.lib user32.lib gdi32.lib advapi32.lib " \
    "shell32.lib ole32.lib oleaut32.lib uuid.lib"

# **************************************************************************************************

class Link(devon.makers.Link):
    path = "link"
    rcPath = "RC"

    def build(self, project, out, sources, target):
        if os.path.basename(target) in project.neverLink:
            return 0

        # Compile any resource files if necessary
        rcArgs = ""
        for name in project.resources:
            command = """%s %s""" % (self.rcPath, name)
            devon.make.executeCommand(project, self, command, out)
            rcArgs += """%s""" % (name.replace("rc", "res"))

        args = self.getBaseArgs(project, sources, target)
        command = '%s /OUT:"%s" %s %s' % (self.path, target, args, rcArgs)
        return devon.make.executeCommand(project, self, command, out)

    def getBaseArgs(self, project, sources, target):
        args = " ".join(sources)
        args += " " + project.linkerFlags

        if project.optimize == "debug":
            args += " /DEBUG"

        if project.linkIncremental:
            args += " /INCREMENTAL"

        args += " /SUBSYSTEM:%s" % project.subSystem
        args += " " + defaultLibs

        for libName in project.getLibs(deep=True, absPaths=True):
            if libName.rfind(".") == -1:
                libName += ".lib"
            args += " " + libName

		# XXXblake Need to add libpaths too... e.g. Python specifies its lib via a pragma,
		# but we still need to include its libpath -- the buildPath specified in user.py

        return args

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class LinkExecutable(Link, devon.makers.LinkExecutable):
    def getTarget(self, project):
        return "%s.exe" % project.name

    def getDependencies(self, project):
        return devon.makers.LinkExecutable.getDependencies(self, project)

    def build(self, project, out, sources, target):
        res = Link.build(self, project, out, sources, target)
        if res:
            return res

        command = '%s /manifest %s.manifest /outputresource:%s;#%d' \
            % (kMtPath, target, target, 1)
        return devon.make.executeCommand(project, self, command, out)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class LinkDynamicLib(Link, devon.makers.LinkDynamicLib):
    regPath = "\\windows\\system32\\regsvr32"
    def getTarget(self, project):
        return "%s.dll" % project.name

    def build(self, project, out, sources, target):
        res = Link.build(self, project, out, sources, target)
        if res:
            return res

        command = '%s /manifest %s.manifest /outputresource:%s;#%d' \
            % (kMtPath, target, target, 2)
        return devon.make.executeCommand(project, self, command, out)

    def getBaseArgs(self, project, sources, target):
        args = Link.getBaseArgs(self, project, sources, target)
        args += " /DLL"
        if project.definition:
            args += (" /DEF:\"%s\"" % project.expandString(project.definition))

        dot = target.rfind(".")
        args += " /IMPLIB:" + target[0:dot] + "_import.lib"
        return args

    def install(self, project, out, sources, target):
        out << tags.Block("progressBox progress-build") << "Registering " \
            << tags.FileLink(path=target) << target << tags.Close \
            << "..." << tags.Close << tags.Flush

        # Hack
        for destinationPath in project.installPaths:
            source = project.installPaths[destinationPath]
            if source == "%(buildTarget)s":
                target = destinationPath + "\\" + target
                break

        # We don't use executeCommand here because regSvr32 doesn't write to stdout
        return os.spawnl(os.P_WAIT, self.regPath, self.regPath, "/s", "\"%s\"" % target)

    def getDependencies(self, project):
        return devon.makers.LinkDynamicLib.getDependencies(self, project)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class LinkStaticLib(Link, devon.makers.LinkStaticLib):
    path = "lib"

    def getTarget(self, project):
        return "%s.lib" % project.name

    def getBaseArgs(self, project, sources, target):
        args = " ".join(sources)
        args += " " + project.linkerFlags
        args += " /SUBSYSTEM:%s" % project.subSystem
        return args

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class LinkTestRunner(LinkExecutable, devon.makers.LinkTestRunner):

    def getBaseArgs(self, project, sources, target):
        args = LinkExecutable.getBaseArgs(self, project, sources, target) \

        # Link in the boot libraries so main() and TestEnvironment are available
        for dep in devon.makers.LinkTestRunner.__getDeps():
            args += " %s" % dep.getBuildTarget()

        return args

    def getDependencies(self, project):
        return devon.makers.LinkTestRunner.getDependencies(self, project)

