
import devon.maker
import time, glob, os.path, re, sys, types, threading

# **************************************************************************************************

projectBuiltin = None
projectCache = {} # path   -> project
exportMap = {}    # export -> projects
projectMap = {}   # name   -> project

kDefaultWikiPath = "docs"
kPrecompiledHeader = "pch"

projectFileName = "project.dev"
projectDepFileName = ".project.dep"
workspaceFileName = "workspace.dev"
userFileName = "user.dev"
pchH = kPrecompiledHeader + ".h"

if sys.platform == "win32":
    defaultInterfaceFlags = "/no_robust"
    defaultCompilerFlags = "/EHsc /Wp64 /nologo /GR"
    defaultLinkerFlags = "/NOLOGO /MACHINE:X86"

else:
    defaultInterfaceFlags = ""
    defaultCompilerFlags = ""
    defaultLinkerFlags = ""

rePrivate = re.compile("__.*?__")

# **************************************************************************************************
# Public API

def load(projectPath = None, recurse = True):
    """Loads the project that lives in a specified directory"""
    
    if projectPath == None:
        projectPath = os.getcwd()
    
    localProjectPath = __findProjectPath(projectPath, recurse)
    if localProjectPath == None:
        # Either the project path is invalid, or it's an external project. If it's external, it
        # should already be in our cache from when we read in the user file.
        if projectPath in projectCache:
            return projectCache[projectPath]
        
        raise Exception("%s is not a valid project path " % projectPath)

    project = __importProject(localProjectPath)
    return project

def loadUserProject():
    """ Loads a project that contains only the contents of user.dev.

        This project will not be cached, so every call will reload it."""

    userFilePath = os.path.join(os.path.expanduser(devon.userPath), userFileName)

    project = DevonProject("", time.time())
    __mergeProject(project, "", userFilePath)
    return project

def getNearestProjectPath(sourcePath):
    projectPath = __findProjectPath(sourcePath)
    if projectPath:
        return os.path.join(projectPath, projectFileName)

def getProjectByName(name):
    if name in projectMap:
        return projectMap[name]
    
    return None
    
def shutdownProjects():
    for project in projectCache.values():
        if isinstance(project, DevonProject):
            project.writeDependencyFile()
        
def loadExternalProjects():
    """ Instantiates each of the external projects found in the user file. """
    
    path = os.path.join(os.path.expanduser(devon.userPath), userFileName)
    locals = __importProjectLocals(path)
    
    for attr in locals:
        obj = locals[attr]
        
        if not isinstance(obj, types.ClassType) \
            or not issubclass(obj, ExternalProject) \
            or obj is ExternalProject:

            continue
           
        # Instantiate the external project. ExternalProject's constructor will
        # do everything else.
        obj = obj()

# **************************************************************************************************

class ProjectBranch:
    def writeBranch(self, projectLocals):
        for name in projectLocals:
            localValue = projectLocals[name]

            if hasattr(self, name):
                selfValue = getattr(self, name)
                if isinstance(selfValue, ProjectBranch):
                    # If the member is a branch object, the project variable is expected to be
                    # a class whose members we copy directly onto the branch
                    if localValue and isinstance(localValue, types.ClassType):
                        selfValue.writeBranch(vars(localValue))
                        continue
            setattr(self, name, localValue)
            
# **************************************************************************************************

class Project:
    name = ""
    
    def __init__(self):
        self.__includePaths = None
    
    def __post_init__(self):
        pass
       
    def __repr__(self):
        return "<project %s (%s)>" % (self.name, self.path)
        
    def getDependencies(self, deep = False, source = None, projects = None, dups = None):
        return []

    def getIncludePaths(self):
        if self.__includePaths is None:
            self.__includePaths = self.getExportPaths()
        return self.__includePaths[:]
         
    def getSourceDependencies(self, source, deep, checkedDeps):
        return []

    def getAbsolutePath(self, relPath):
   
        """ Joins the project path with the relative path and returns the absolute path. Does not
            check to see if the path exists. """
            
        return os.path.join(self.path, relPath)

    def getAbsolutePaths(self, relPaths):
        
        """ Returns a list of absolute paths given a list of relative paths.
            This is just a convenience function; see getAbsolutePath() above
            for the dirty work. """
        
        return [self.getAbsolutePath(relPath) for relPath in relPaths]

    def getExportPaths(self, deep = False, absPaths = True):
        """ Returns a list of the project's export paths. An export path contains
            files that other projects may include.
            
            There are two kinds of export paths: the real export path, which
            reflects the actual directory structure, and the virtual export
            path, which is the path that other projects use. For example, a
            project may export the directory /foo/shared/thread/include,
            containing foopy.h, as the virtual path suade/thread, such that
            clients would include suade/thread/foopy.h. Behind the scenes, virtual
            paths are symlinks in the build directory. This allows us to have nice
            include namespaces that we can use to look up the exporting project,
            without having to muck up the directory structure.
            
            Because the actual location of the exported files is an unnecessary
            detail, this function only supplies virtual paths.
            
            A project is not required to use virtual paths, in which case we
            export the parent of the real path. In other words, if a project
            exports /foo/shared/thread/Thread containing bar.h, we export
            /foo/shared/thread, and a client project would include
            <Thread/bar.h>.
            
            If absPaths is True, this function returns the absolute export paths
            that can be handed to the compiler as include paths. If False, it
            it returns the paths the client uses, such as "suade/thread".
            
            If deep is True, the returned list includes exported subfolders as
            well. For example, if a project exports /foo/shared/thread/Thread
            containing subfolder Primitives and you request client paths, this
            function returns ["Thread", "Thread/Primitives"]. """

        paths = []
        
        for relRealPath in self.exports:
        
            # Ensure that the real export path actually exists
            absRealPath = self.getAbsolutePath(relRealPath)
            if not os.path.exists(absRealPath):
                raise OSError, "Export path %s does not exist" % absRealPath
          
            # absIncludePath below represents the directory containing the
            # exports, since that's actually the path we export. In other words,
            # if a client project is to include foopy/bar/baz.h as bar/baz.h,
            # we need to export foopy.
            
            relVirtualPath = self.exports[relRealPath]
            if relVirtualPath:
                absIncludePath = self.getBuildPath()
                
                linkPath = os.path.join(absIncludePath, relVirtualPath)
                # XXXblake Need to check symlink target against expected target
                # and recreate if they don't match; the symlink could exist,
                # but point to the wrong place
                if not os.path.exists(linkPath):
                
                    # All directories up until the actual link must exist
                    dir = os.path.dirname(linkPath)
                    if dir and not os.path.exists(dir):
                        os.makedirs(dir)
                    
                    # Finally, create the actual link target to absRealPath
                    try:
                        os.symlink(absRealPath, linkPath)
                    except Exception,exc:
                        print "ERROR: unable to link", absRealPath, "to", linkPath
                    
                relIncludePath = relVirtualPath
            else:
                # XXXblake This isn't right. Consider libxml2, which by default installs headers to
                # /usr/include/libxml2/libxml/. If a user file specifies
                #       exports = { "include/libxml2" : None }
                # we should be exporting everything in /usr/include/libxml2, and thus
                # include <libxml/*.h should work...to make this work, we have to enumerate the dirs
                # in the export path and add those to our list. The code below will add libxml2 to
                # our export map and export include/
                absIncludePath, relIncludePath = os.path.split(absRealPath)
            
            if absPaths:
                includePath = absIncludePath
            else:
                includePath = relIncludePath
                          
            if not includePath in paths:
                paths.append(includePath)
        
            # If it's an external project, we grudgingly add the non-namespaced export path as well,
            # since the project's own files won't use the namespace. For example, if the exported
            # path is include/libxml2, we would normally export include and force clients to include
            # libxml2/*.h. But since libxml2's own headers won't do that, we'll also export
            # include/libxml2.
            if absPaths and isinstance(self, ExternalProject):
                paths.append(absRealPath)

            if deep:
                arpLength = len(absRealPath)
                for root, dirs, files in os.walk(absRealPath):
                    length = len(dirs)

                    for i, dir in enumerate(reversed(dirs)):
                        if not includeSource(root, dir, False):
                            del dirs[length-i-1]
                            continue
                        
                        # Get the relative path (e.g. "win")
                        relPath = os.path.join(root, dir)[arpLength:]
                        if absPaths:
                            includePath = os.path.join(absRealPath, relVirtualPath, relPath)
                        else:
                            includePath = os.path.join(relVirtualPath, relPath)

                        if not includePath in paths:
                            paths.append(includePath)
        return paths
    
    def makeVirtual(self, source):
        """ Given an absolute or relative concrete export path, returns the
            same path with symlinks if possible. """
        
        if os.path.isabs(source):
            absPaths = True
            relPath = self.getRelativePath(source)
        else:
            absPaths = False
            relPath = source
            
        # If not, enumerate our real paths until we find which one this is    
        for realPath in self.exports:
            virtualPath = self.exports[realPath]
            if not virtualPath:
                continue

            if os.path.dirname(relPath) == realPath:
                path = os.path.join(virtualPath, os.path.basename(source))
                if absPaths:
                    path = self.getAbsolutePath(os.path.join(realPath, kVirtualExportDir, path))
                return path
                
        # Can't be virtualized, so return the original source.
        return source
        
    def makeConcrete(self, source):
        """ Given an absolute or relative export path, returns the same path
            without symlinks. This is similar to os.path.realpath(), but it's
            much faster because it only works for known export paths.
            
            Examples:

            INPUT                                  OUTPUT
            
            <Absolute Paths>
            
            /foo/shared/base/Suade/base/foopy.h  /foo/shared/base/include/foopy.h
                       
            <Relative Paths>
            
            Suade/base/foopy.h                      include/foopy.h
            
        """

        if os.path.isabs(source):
            relSrcPath = self.getRelativePath(source)
            absPaths = True
        else:
            relSrcPath = source
            absPaths = False
        
        # Enumerate our real path -> virtual path mapping until we find the corresponding virtual
        # path, then splice in the real path in its place.
        for relRealPath in self.exports:
            relVirtualPath = self.exports[relRealPath]
            if relVirtualPath:
                rvpLen = len(relVirtualPath)
                
                # See if the source path begins with the real path. We have to check for a trailing
                # slash to ensure we're actually matching directories. If we just compared rvpLen
                # letters, we'd consider e.g. "DevonLog/Foopy.h" to match an export path of "Devon"
                if relSrcPath[:rvpLen+1] == (relVirtualPath + "/"):
                    source = os.path.join(relRealPath, relSrcPath[rvpLen+1:])
                    
                    if absPaths:
                        source = self.getAbsolutePath(source)
                    
                    break
            else:
                # No virtual path specified. That means we're exporting the
                # directory itself, so check and see if the head of the real path
                # + the head of the source path exists. In other words, say the
                # project exported { "foopy/bar": None } given foopy/bar/baz/blah.h
                # and the source path is <bar/baz/blah.h>.
                # XXXblake Not really making concrete here...
                
                relPath = os.path.join(os.path.dirname(relRealPath), relSrcPath)
                absPath = self.getAbsolutePath(relPath)

                if os.path.exists(absPath):
                    if absPaths:
                        source = absPath
                    else:
                        source = relPath
                    break
                
        return source       

    def getRelativePath(self, absPath, throw=True):        
        """ Extracts the project path from an absolute path and returns the relative path."""
        
        if not absPath.lower().find(self.path.lower()) == 0:
            if throw:
                raise ValueError, "Supplied source is not part of this project"
            return None

        length = len(self.path)
        if not self.path[-1] == "/":
            length += 1
        return absPath[length:]

    __includePaths = None
    
class ExternalProject(Project):
   
    def __init__(self):
        """ Adds the project's exports to the global export map, and the project
            itself to our global project cache. ExternalProjects are only
            instantiated by loadUserSettings() in web.py """
              
        Project.__init__(self)
                  
        if not self.path:
            if sys.platform == "win32":
                raise "No path specified for external project ", self.name
            
            self.path = "/usr"
            
        # XXXblake Doesn't seem like the right place to do this    
        populateExportMap(self)               
        projectCache[self.path] = self
        projectMap[self.name] = self
        
    def getBuildTarget(self):
        build = None
        
        # `build` can be unspecified, True, False, None or a filename. If unspecified or True, we'll
        # attempt to locate a file matching the project's name. If False or None, the project is not
        # built. If a filename is specified, we'll just use that filename.
        if not hasattr(self, "build") or self.build == True:
            build = self.name
        elif self.build:
            build = self.build
        else:
            return
                        
        # XXXblake I think external projects actually need a getBuildTargetS(),
        # and we should just try to link all of its libraries. You shouldn't have
        # to specify manually.
        # targets = [] 
        # for source in getSourcesIn(self.getBuildPath(), absPaths=True):
        #     if source[-4:].lower() == ".lib":
        #         targets.append(source)
        # return targets
        if sys.platform == "win32":
            if build.find(".") == -1:
                build += ".lib"
            path = self.getBuildPath(build)
        else:

            def getLibPath(name):
                if sys.platform == "darwin":
                    fullName = "lib%s.dylib" % name
                else:
                    fullName = "lib%s.so" % name # XXXblake Version numbers (e.g. .so.2)?
                
                path = self.getBuildPath(fullName)
                if not os.path.exists(path):
                    path = self.getBuildPath("lib%s.a" % name)
                
                return path
                
            if build.find(".") == -1:
                path = getLibPath(build)
            else:
                path = self.getBuildPath("lib%s" % build)
                
                # The dot may not necessarily indicate an extension (e.g. "libpython2.4")
                if not os.path.exists(path):
                    path = getLibPath(build)

        # XXXblake REQUIRE(os.path.exists...)
        
        if not os.path.exists(path):
            # Couldn't find the build target, but this is only an error if the developer indicated
            # that he expects one--by specifying build = True, build = <filename>, or a buildPath.
            if (hasattr(self, "build") and self.build) or self.buildPath:
                raise "Invalid path (%s) for external project %s" % (path, self.path)
                
            return
        
        return path
        
    def getName(self):
        classname = str(self.__class__)
        return classname[classname.rfind(".")+1:]
        
    def getBuildPath(self, targetPath = None):
        buildPath = self.getAbsolutePath(self.buildPath or "lib")
        if targetPath:  
            return os.path.join(buildPath, targetPath)
        
        return buildPath
                      
    name = property(getName)
    path = None
    buildPath = None
    libs = []
        
    def getFrameworks(self, deep=False):
        return {}

class DevonProject(Project, ProjectBranch):
    def __init__(self, path, updateTime):
    
        Project.__init__(self)
        
        # Use forward slashes since this gets printed to streams in many places
        # and it's easier than trying to escape it everywhere
        self.path = os.path.abspath(path).replace("\\", "/")
        self.updateTime = updateTime
        self.projectFilePaths = []
        
        self.userName = ""
        self.password = ""
        
        self.name = None
        self.version = None
        self.description = None
        self.url = None
        self.author = None
        self.authorEmail = None
        
        self.glossary = {}
        
        self.defaultProject = None
        self.wikiPath = kDefaultWikiPath
        
        self.buildPath = None
        self.buildRootPath = None
        self.buildProject = self
        
        self.buildPre = []
        self.build = None
        self.buildPost = []
        
        self.deps = {}

        self.dist = None
        self.distInstallPaths = None

        self.exclude = []
        self.debugSources = []
        self.installPaths = {}
        self.pythonModules = []

        import devon.builtin
        self.buildTests = devon.builtin.CompileTestRunner() >> devon.builtin.LinkTestRunner()
        self.alwaysBuild = [] # Source files to rebuild every time
        self.neverLink = [] # Target files to never link
        
        # Libraries to link against. This should be used only for system libs
        # in cases where we can't determine library from the include alone. For
        # example, the include for many Windows libraries is the generic
        # <windows.h>
        # XXXblake I think in the future we should require a comment next to
        # such includes that we'll parse, then remove this, e.g.:
        #   #include <windows.h> // gdiplus, timer
        # The code should be self-documenting like that.
        self.libs = []
        self.resources = []
        self.frameworks = []
        self.ignoreFrameworks = []
        
        self.frameworkPaths = []
        self.exports = {}
        
        self.optimize = "debug"
        self.warningLevel = 4
        self.pedantic = False
        
        pch = self.getAbsolutePath(pchH)
        if os.path.exists(pch):
            self.pch = pchH
        else:
            self.pch = None

        self.debug = True
        self.debugCommand = None
        self.debugArgs = None
        self.debugPath = None
        
        self.testExcludes = []
        self.testRunner = None

        self.pythonExes = {}
        self.pythonPaths = []
        
        self.showCommands = False
        self.formatOutput = True
        
        self.linkerFlags = defaultLinkerFlags
        self.compilerFlags = defaultCompilerFlags
        self.interfaceFlags = defaultInterfaceFlags

        # ******************************************************************************************

        self.defines = ProjectBranch()
        self.config = ProjectBranch()
        self.wiki = ProjectBranch()
        self.buildArguments = ProjectBranch()
        self.distArguments = ProjectBranch()
        
        if not sys.platform == "darwin" and not sys.platform == "win32":
            self.defines._REENTRANT = True

        # ******************************************************************************************
        # Win32 Options

        if sys.platform == "win32":
            # Compiler options
            # Use the multithreaded CRT by default; msvc requires runtime libs to be the same type
            self.runtimeThreaded = True

            # Linker options
            self.linkIncremental = True
            self.definition = None # http://msdn.microsoft.com/library/default.asp?url=/library/en-us/vccore/html/_core_module.2d.definition_files.asp

            self.subSystem = "CONSOLE"
            
            self.defines.WIN32 = True
            self.defines._WINDOWS = True
            self.defines._WIN32_DCOM = True
            self.defines._WIN32_WINNT = 0x0501
            self.defines._MBCS = True
            
        # ******************************************************************************************
        # Mac OS X options
        
        elif sys.platform == "darwin":

            self.defines.DARWIN = True
            
            # App Bundle options
            self.executableFile = None
            self.plistFile = None
            self.iconFile = None
            self.signature = None
            self.osFiles = None
            self.resourceFiles = None
        
        # ******************************************************************************************
        # Firefox Extension options
    
        self.installScript = None
    
        # ******************************************************************************************
        # Mozilla Jar options
        
        pass
     
    def __post_init__(self):
        
        """ Called after the project file is reflected onto the Project instance. """
        
        self.__dependencyFile = self.getBuildPath(projectDepFileName)
     
        # If a name in the exclusion list has no extension and it's not a child
        # project, we assume exclusion of both the source file and its associated
        # header (if any).
        
        for i, exclude in enumerate(self.exclude):
            excludeRelPath = exclude
            exclude = self.makeConcrete(self.getAbsolutePath(exclude))
            
            # Skip over anything with an extension
            if exclude.rfind(".") > -1:
                self.exclude[i] = exclude
                continue
            
            # XXXblake Just use glob    
            # Check if it's a project
            path = os.path.join(exclude, projectFileName)
            if os.path.exists(path):
                self.exclude[i] = exclude
                continue
            
            # Otherwise, if it's a source file, exclude associated include
            cpp = "%s.cpp" % exclude
            if os.path.exists(cpp):
                self.exclude[i] = cpp
                
                for export in self.exports: 
                    header = os.path.join(self.path, export, "%s.h" % excludeRelPath)
                    if os.path.exists(header):
                        self.exclude.append(header)
                        break

    def writeBranch(self, projectLocals):
        # Copy all of the variables from the project file onto the project object
        # if they are in the set of pre-defined project member variables
        for name in vars(self):
            if name in projectLocals:
                selfValue = getattr(self, name)
                localValue = projectLocals[name]
                
                if isinstance(selfValue, ProjectBranch):
                    # If the member is a branch object, the project variable is expected to be
                    # a class whose members we copy directly onto the branch
                    if localValue and isinstance(localValue, types.ClassType):
                        selfValue.writeBranch(vars(localValue))
                
                else:
                    setattr(self, name, localValue)

    def getParentProject(self):
        parentPath = os.path.dirname(self.path)
        if not parentPath or not os.path.isdir(parentPath):
            return None
        
        try:
            return load(parentPath)
        except:
            return None

    def getChildProject(self, projectPath):
        childPath = os.path.join(self.path, projectPath)
        if not os.path.isdir(childPath):
            return None
        
        return load(childPath, False)

    def getChildProjects(self, deep = False):

        """ Compiles a list of the specified project's child projects """

        allExclude = [self.buildRootPath]
        
        def getProjectsUnderPath(path, deep, projectExclude = []):
            """ Returns a list of the projects that live below the specified path. The
                optional exclude list should contain absolute project paths. """

            projects = []
            
            for name in os.listdir(path):
            
                if name[0] == "." or name == "docs":
                    continue
                    
                full = os.path.join(path, name)
                if not os.path.isdir(full) or full in projectExclude or full in allExclude:
                    continue

                # Respect platform forks
                if name == "mac" and sys.platform != "darwin":
                    continue

                if name == "win" and sys.platform != "win32":
                    continue

                if name == "unix" and sys.platform == "win32":
                    continue

                project = None
                projectPath = os.path.join(full, projectFileName)
                if os.path.exists(projectPath):
                    project = load(projectPath)                    
                    projects.append(project)   
                    
                    # Don't bother walking this project's build directory. We add the path to
                    # our "all exclude" list, since it's not necessarily a direct child of the
                    # project; it could be anywhere.
                    buildPath = project.buildRootPath
                    if not buildPath in allExclude:
                        allExclude.append(buildPath)

                if deep:
                    if project:
                        exclude = project.exclude
                    else:
                        exclude = []
                    projects.extend(getProjectsUnderPath(full, True, exclude))

            return projects    
            
        return getProjectsUnderPath(self.path, deep, self.exclude)
        
    def getBuildTarget(self):
        """Gets the path of the build target for a ManyToOne project"""
        
        if not self.build or isinstance(self.build, devon.maker.MakerOneToOne):
            return None
            
        targetPath = self.build.getTarget(self)
        return self.getBuildPath(targetPath)

    def getBuildPath(self, targetPath=None):
        """ Gets the full path of a single target in the build directory of the build project.
            All returned paths end with trailing slashes. """
        
        if self.path.find(self.buildProject.path) == 0:
            relativePath = self.path[len(self.buildProject.path)+1:] # +1 for the trailing slash
            session = getSession()           
            basePath = os.path.join(self.buildRootPath, getPlatformAbbreviation())
            if hasattr(session, "buildDir"):                
                basePath = os.path.join(basePath, session.buildDir)
            basePath = os.path.join(basePath, relativePath)
        else:
            raise "Not currently supported/tested"
        
        if targetPath:
            return os.path.join(basePath, targetPath)
                      
        return basePath
    
    def getDocumentPath(self, docName):
        docName = docName.replace("_", " ")
        return os.path.join(self.path, self.wikiPath, "%s.txt" % docName)
       
    def getSources(self, includeDirs = False, includeTests = False, absPaths = False, changedAfter = 0,
        types = []):
    
        """ Returns a project's sources, which basically consists of every file
            within the project directory and each of its subdirectories until
            another built project is reached. In other words, given
            
                /foopy/
                      base/
                          project.dev
                          blah.cpp
                          blah.h
            
            this function would return ["blah.cpp", "blah.h"] for the base
            project and [] for the top-level foopy project. """
                            
        excludes = self.exclude
        if not getSession().debug:
            excludes += self.getAbsolutePaths(self.debugSources)
        return getSourcesIn(self.path, includeDirs, includeTests, absPaths, excludes, changedAfter, types)    
       
# **************************************************************************************************
# Test

    def getTestSources(self, includeDirs = False, absPaths = False):
        sources = getSourcesIn(self.getAbsolutePath("tests"), includeDirs, absPaths)
        
        # getSourcesIn() returns paths relative to the test dir. If the caller is
        # expecting paths relative to the project path, fix up the paths here.
        if not absPaths:
            sources = [os.path.join("tests", source) for source in sources]
        
        return sources
        
# **************************************************************************************************
# Dependencies

    def getLibs(self, deep=False, absPaths=False):
        """ Retrieves the project's dependent libraries. By default, a complete
            list of library names (e.g. "foopy.lib") is returned, including
            system libraries, such as gdi.lib. If absPaths is specified, we may
            not be able to return the absolute paths of all explicit libs,
            particularly system libraries.
        """
        # XXXblake This is temporary pending ExternalProject.getBuildTargetS()
        def getAbsPathsOfExplicitLibs(explicitLibs):
            libs = []
            for lib in explicitLibs:
                # XXXblake Make getExportingProject() just take the export path,
                # since we end up indexing slash again below
                project = getExportingProject(lib)
                if project: # XXXblake Not currently checking dups...is it faster to just pass dups to the linker?
                    libs.append(project.getBuildPath(lib[lib.rfind("/")+1:]))
                else:
                    libs.append(lib)
            return libs

        if absPaths:
            libs = getAbsPathsOfExplicitLibs(self.libs)
        else:        
            libs = self.libs[:]

        # XXXblake getDependencies() should probably also return any projects
        # culled from our explicit libs list
        
        for dep in self.getDependencies(deep):
            depExplicitLibs = dep.libs
            if absPaths:
                depExplicitLibs = getAbsPathsOfExplicitLibs(depExplicitLibs)
            libs.extend(depExplicitLibs)

            target = dep.getBuildTarget()
            if target:    # If the project is built 
                if absPaths:
                    lib = target
                else:               
                    lib = os.path.basename(target)

                # XXXblake Do we really need this check if getDependencies() already does dup-checking?
                if not lib in libs:
                    libs.append(lib)
                
        return libs
        
    def getLibPaths(self, deep=False):
        """ Retrieves the project's absolute library paths """

        libPaths = []
        libs = self.getLibs(deep, True)
        for lib in libs:
            libPaths.append(os.path.dirname(lib))
            
        return libPaths
        
    def getIncludePaths(self, deep = False, source = None):
        """ Retrieves the project's absolute include paths. """

        includes = Project.getIncludePaths(self)
        includes.append(self.path)

        if deep:
            for dep in self.getDependencies(deep, source):
                for include in dep.getIncludePaths():
                    if not include in includes:
                        includes.append(include)

        return includes

    # XXXblake Seems like a lot of the complexity would disappear if we stored concrete paths in the
    # dependency lists in a tuple that also contains the project name (rather than storing virtual
    # paths just so we can retrieve the exporting project)
    
    
    # XXXblake This function is currently not used because the headersOnly method of retrieving
    # dependencies is faster.
    def getSourceIncludePaths(self, source, deep = False):
    
        """ Retrieves the source's absolute include paths. The specified source should be relative
            to the project. """
        
        includes = []
        projects = []
        sources = []
                
        def getIncludes(project, source, deep):
        
            if source in sources:
                return includes
            sources.append(source)
            
            project.__updateDependencies()
            for dep in project.deps[source]:
                depProject = getExportingProject(dep)
                
                if not depProject:
                    if dep in project.deps:
                        # If there's no exporting project but the source is in our own list, it must
                        # be a local project include
                        depProject = project
                    else:
                        # Otherwise, could be a system include, e.g. <string>
                        continue
                    
                if not depProject in projects:
                    for include in depProject.getIncludePaths():
                        if not include in includes:
                            includes.append(include)
                    projects.append(depProject)
                    
                # Only retrieve includes for Devon projects for now, since we don't currently have
                # a concept of dependencies tracking for external projects (XXXblake)
                if deep and isinstance(depProject, DevonProject):  
                    source = depProject.makeConcrete(dep)
                    getIncludes(depProject, source, deep)
            
            return includes         
                       
        return getIncludes(self, source, deep)
        
    def readDependencyFile(self):    
        """ Load the dependency map from the project's dependency file """

        path = self.__dependencyFile
        if not os.path.exists(path):
            self.__updateDependencies()
        else:
            f = {}
            execfile(path, {}, f)
            self.deps = f["deps"]

    def writeDependencyFile(self):
        """ Write the dependency map to the project's dependency file """
        
        dir = os.path.dirname(self.__dependencyFile)
        if not os.path.exists(self.__dependencyFile) and not os.path.exists(dir):
            os.makedirs(dir)
            
        f = file(self.__dependencyFile, "w")
        f.write("deps = {")
        for source, deps in self.deps.iteritems():
            f.write("'%s': [" % source)
            for dep in deps:
                f.write("'%s'," % dep)
            f.write("],")
        f.write("}")

    def __updateDependencies(self):    
        """ Ensures that our in-memory and written dependency map is completely
            up to date. Note that we currently use the dependency file's time
            stamp--rather than a per-source timestamp--as the sole indicator of
            whether a source's dependency listing needs updating. This means that
            whenever a source has changed and we update its dependencies, we
            need to ensure that all other source dependency lists are up to date
            as well. """
            
        # Note: We don't strip tests for now, because a test source might create a
        # dependency that none of the actual sources do, so we need to find those
        # too. In the future, we may actually wish to offer a separate "test project"
        # that offers getIncludePaths(), getSources(), etc.  

        # XXXblake Rather than doing this check, create the file and utime(0) earlier
        # XXXblake Why use the dependency file time as the marker instead of an in-memory flag?
        if os.path.exists(self.__dependencyFile):
            depLastMod = os.path.getmtime(self.__dependencyFile)
        else:
            depLastMod = 0
            
            # Clear the in-memory map so we don't write old cruft if you delete a dependency file
            # while the server is running
            self.deps.clear()

        source = None
        types = ["cpp", "h", "c", "hpp", "hxx", "mm", "lex", "y"]
        for source in self.getSources(absPaths=True, changedAfter=depLastMod, includeTests=True, types=types):
            self.deps[self.getRelativePath(source)] = getIncludes(source)
      
        # If we updated the in-memory dependency map, just touch it and we'll write it on shutdown,
        # unless we've never created the dependency file before, in which case we'll write it now
        if source:
            if not depLastMod:
                self.writeDependencyFile()
            os.utime(self.__dependencyFile, None)

    def getSourceDependencies(self, source, deep = False, checkedDeps = None):
        
        """ Yields the source's include dependencies. Takes either an absolute
            or relative source path. Since a source's dependencies usually come
            from a mix of projects, this function always returns absolute paths. """
        
        if os.path.isabs(source):
            # Ensure that the source is actually part of this project by trying
            # to retrieve a relative path.
            relSrcPath = self.getRelativePath(source, throw=False)
            
            # If the source isn't in the project path, it might be a file in
            # our build directory. Not quite sure how to handle this right now.
            # It seems like we should be able to extract dependency information
            # from generated files--consider e.g. a file that gets preprocessed
            # into a source file. In fact, that's how flex/bison files work
            # right now, but we get lucky there in that their original files
            # have includes of the proper format. For now, we'll just check
            # if this is a build file and return an empty list if so.
            if not relSrcPath:
                buildPath = self.getBuildPath()
                if source[:len(buildPath)] == buildPath:
                    return
                raise ValueError, "Supplied source is not part of project"
                
        else:
            relSrcPath = source
            source = self.getAbsolutePath(source)
            
        if checkedDeps is None:
            checkedDeps = []
               
        # XXXblake Check ctime (which is creation time on Windows) everywhere
        if not os.path.exists(self.__dependencyFile) or \
                os.path.getmtime(source) > os.path.getmtime(self.__dependencyFile):
            self.__updateDependencies()

        if not relSrcPath in self.deps:
            raise "Couldn't retrieve dependency information for ", relSrcPath
                
        for dep in self.deps[relSrcPath]:

            if dep in checkedDeps:
                continue
            
            checkedDeps.append(dep)

            project = getExportingProject(dep)
            path = None
            if not project:
                # Note that it's entirely possible for a local file to match the name of an external
                # file. Since we've lost the <> versus "" information in the include directive, we'll
                # just forge ahead knowing we might be wrong. Usually the worst that happens is that
                # we unnecessarily rebuild a source file, but since it also affects getDependencies(),
                # it could cause incorrect lib/include paths, etc. If this becomes an issue, we could
                # prevent this by prepending something (e.g. "./") in getIncludes when we parse a
                # quoted include. In other words, given local subfolder "gecko" and external project
                # "gecko", we'll mistake "gecko/foopy.h" as a gecko-project reference. Or given
                # <system/file.h> and local system subfolder, we'll mistake it as a self-reference.
                # The latter case is less concerning since it's just the self project again.
                path = self.getAbsolutePath(dep)
                if os.path.isfile(path):
                    project = self
                else:
                    # OK, the header isn't at the base of the project. Before giving up, see if it's
                    # relative to the current file.
                    dirname = os.path.dirname(relSrcPath)
                    if dirname:
                        rel = os.path.join(dirname, dep)
                        path = self.getAbsolutePath(rel)
                        
                        # We check that rel is in self.deps below to guard against a scenario such as
                        # that presented by shared/thread/include/Semaphore.h, which includes the
                        # posix <semaphore.h>, and which we would otherwise treat as the local header
                        # only to bail on the next call when we can't find dependency information for
                        # include/semaphore.h. The correct fix here is probably to retain the
                        # important metadata provided by the choice of "" versus <> for includes, as
                        # discussed above.
                        if os.path.isfile(path) and rel in self.deps:
                            project = self
                            dep = rel

            if not project:
                continue
                
            # Now we need to turn the virtual path into a real path so we can
            # get an absolute path, and so we can call ourselves recursively
            # if deep was requested.
            
            if not path:
                dep = project.makeConcrete(dep)
                path = project.getAbsolutePath(dep)

            # It's possible that a given dependency no longer exists, e.g. if
            # a header has been renamed but nobody updated the source file. Since
            # we won't recompile the file (and thus induce the compiler to catch
            # the error) unless the source file happened to change for other reasons,
            # we'll throw and cause the buck to stop here.

            if not os.path.exists(path):
                raise ValueError, "%s does not exist; did you rename a header \
                    file and forget to update the source file?" % path

            yield path
                           
            if deep:   
                for dep in project.getSourceDependencies(dep, deep, checkedDeps):
                    yield dep
       
    def getDependencies(self, deep = False, source = None, projects = None):
        """ Returns a list of the project's dependent projects. """
      
        # XXXblake The "source" param is a big, big hack. Basically what we're doing is calculating
        # one source's dependencies by retrieving all the *potential* dependencies, i.e. anything
        # exported by a project that exports one of the source's dependencies, recursively.
              
        if projects is None:
            projects = []

        # Ensure the dependency map is up-to-date
        self.__updateDependencies()

        # Now flatten the dependency map into a list, retrieve the project from
        # the dependency, and, if requested, get each dependency's dependencies

        for src, deps in self.deps.iteritems():
            if source and src[-2:] not in (".h", ".y") and not src[-3:] == ".lex" \
                    and not src == source:
                continue
            
            for dep in deps:
                project = getExportingProject(dep)
                
                # Don't include ourselves or duplicates in the dependency list
                if project and project is not self and not project in projects:
                    yield project
                    projects.append(project)

                    # XXXblake Profile to see if breadth approach (myProjects list) is faster
                    if deep:
                        for proj in project.getDependencies(deep, bool(source), projects):
                            yield proj
        
                
# **************************************************************************************************

    def getFrameworks(self, deep=False):
        names = self.frameworks
        
        if deep:
            for depProject in self.getDependencies(deep):
                for libName in depProject.getFrameworks():
                    if libName not in names and libName not in self.ignoreFrameworks:
                        names.append(libName)
        
        return names

    def expandString(self, path):
        return path % ProjectVariables(self)
        
    def getInheritableProperty(self, name, default):
        value = getattr(self, name)
        if value:
            return value, self
        else:
            parent = self.getParentProject()
            if not parent:
                return default, None
            else:
                return parent.getInheritableProperty(name, default)
            
    def getPathList(self, sources):
        fullSources = []
        if sources:
            cwd = os.getcwd()
            os.chdir(self.path)
    
            for source in sources:
                source = self.expandString(source)

                # On Windows, glob can return paths with backslashes. We change
                # back to forward slashes to maintain the path integrity.
                fullSources += [s.replace("\\", "/") for s in glob.glob(source)]
             
            os.chdir(cwd)

        return fullSources        

# **************************************************************************************************

class ProjectVariables:
    """A wrapper that can used to embed project variables in formatted strings"""
    
    def __init__(self, project):
        self.project = project
    
    def __getitem__(self, name):
        if name == "buildTarget":
            return self.project.getBuildTarget()
        
        elif name == "buildPath":
            return self.project.getBuildPath()
        
        elif name.find("buildTarget_") == 0:
            projectPath = name[12:]
            childProject = self.project.getChildProject(projectPath)
            if childProject:
                return childProject.getBuildTarget()
            else:
                parentPath = os.path.basename(self.project.path)
                projectPath = os.path.abspath(os.path.join("..", projectPath))
                siblingProject = load(projectPath)
                if siblingProject:
                    return siblingProject.getBuildTarget()

        elif name.find("buildPath_") == 0:
            projectPath = name[10:]
            childProject = self.project.getChildProject(projectPath)
            if childProject:
                return childProject.getBuildPath()
            else:
                parentPath = os.path.basename(self.project.path)
                projectPath = os.path.abspath(os.path.join("..", projectPath))
                siblingProject = load(projectPath)
                if siblingProject:
                    return siblingProject.getBuildPath()
                
        else:
            names = name.split(".")
            obj = self.project
            for name in names:
                obj = getattr(obj, name)
            return str(obj)

# **************************************************************************************************

class Session:
    pass

def getSession():
    thread = threading.currentThread()
    if not hasattr(thread, "session"):
        thread.session = Session()
        thread.session.debug = True
        thread.session.optimize = None
        thread.session.buildDir = "debug"
        
    return thread.session
    
# **************************************************************************************************

def __findProjectPath(path, recurse = True):
    """Returns the path of the project that lives in |path|. If no project is
       found and |recurse| is true, this searches the parents of a directory
       until a project file is found"""
    
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        path = os.path.dirname(path)

    while 1:
        projectPath = os.path.join(path, projectFileName)
        if os.path.exists(projectPath):
            return os.path.dirname(projectPath)
        elif recurse:
            newPath = os.path.dirname(path)
            if newPath == path: # We've hit the drive root
                break
            else:
                path = newPath
        else:
            break

    return None
    
def __importProject(projectPath):
    projectFilePath = os.path.join(projectPath, projectFileName)
    workspaceFilePath = os.path.join(projectPath, workspaceFileName)
    userFilePath = os.path.join(os.path.expanduser(devon.userPath), userFileName)
    
    # Look for the project in the cache
    project = None
    if projectPath in projectCache:
        project = projectCache[projectPath]
        
        # If any of the files have been changed, invalidate and reload the project
        for path in (projectFilePath, workspaceFilePath, userFilePath):
            if os.path.isfile(path):
                fileTime = os.path.getmtime(path)
                if fileTime > project.updateTime:
                
                    # Sanity check: if the file time is greater than time.time(), something's wacky.
                    # (I ran into this problem running a Unix VM, where the Unix "hardware clock"
                    # was off and thus invariably fileTime > updateTime and we recursed infinitely.)
                    if fileTime > time.time():
                        raise "Error: System clock appears to be set inappropriately " \
                              "(while importing project %s)" % project.path
                        
                    project = None
                    break
    
        # If we have the wrong project configuration loaded, invalidate and reload
        if project and ((project.debug and not getSession().debug) \
                or (not project.debug and getSession().debug)):
            project = None
            
    if project:
        return project
    
    project = DevonProject(os.path.dirname(projectFilePath), time.time())
    projectCache[projectPath] = project
       
    # Merge the project file
    __mergeProject(project, projectPath, projectFilePath)
    
    # Merge the local workspace file
    __mergeProject(project, projectPath, workspaceFilePath)

    # Merge the user file
    __mergeProject(project, projectPath, userFilePath)

    # Find the project that hosts the build directory and cache it on this project
    if project.buildPath:
        if os.path.isabs(project.buildPath):
            project.buildRootPath = project.buildPath
        else:
            project.buildRootPath = project.getAbsolutePath(project.buildPath)
    else:
        buildPath, buildProject = project.getInheritableProperty("buildPath", ".")
        if buildProject:
            project.buildRootPath = os.path.join(buildProject.path, buildPath)
            project.buildProject = buildProject
        else:
            project.buildRootPath = buildPath
            project.buildProject = project

    # Merge the workspace file for the whole project
    if project.buildProject and not project.buildProject == project:
        rootWorkspacePath = os.path.join(os.path.basename(project.buildProject.path), \
            workspaceFileName)
        __mergeProject(project, projectPath, rootWorkspacePath)
    
    # "Post initialize" the project so it has a chance to do additional work
    # after the project file has been read in
    project.__post_init__()
    
    # Add the project's exports to our global export map
    populateExportMap(project)
    
    # Add the project to our global name map
    projectMap[project.name] = project

    # Read in cached dependencies if the project is built or if it exports
    if isinstance(project, DevonProject) and (project.getBuildTarget() or project.exports):
        project.readDependencyFile()
    
    return project

def __mergeProject(project, projectPath, projectFilePath):
    projectLocals = __importProjectLocals(projectFilePath)
    if projectLocals:
        project.writeBranch(projectLocals)
        
def __importProjectLocals(projectFilePath):
    if not os.path.isfile(projectFilePath):
        return {}

    cwd = os.getcwd()
    os.chdir(os.path.dirname(projectFilePath))

    projectLocals = {}
    projectLocals.update(__getProjectBuiltin())
    projectLocals["debug"] = getSession().debug

    execfile(projectFilePath, {}, projectLocals)
    
    os.chdir(cwd)

    return projectLocals
        
def __getProjectBuiltin():
    global projectBuiltin
    if not projectBuiltin:
        projectBuiltin = {}
        
        import devon.builtin
        for name in vars(devon.builtin):
            if not rePrivate.match(name):
                value = getattr(devon.builtin, name)
                if not type(value) == types.ModuleType:
                    projectBuiltin[name] = value
        
    return projectBuiltin

# **************************************************************************************************
# Dependency Helpers

# reInclude = re.compile(r"""#include (?:(?:"|<)((?:\w*/\w*)*\(?:.h|.hxx|.hpp))(?:"|>))|(?:(?:\")(\w*\(?:.h|.hxx|.hpp)(?:\"))""") 
reInclude = re.compile(r"""#include (?:"|<)(.*?(?:\.h|\.hpp|))(?:"|>)""")
reNamespace = re.compile(r"namespace \w* {")

def populateExportMap(project):

    """ Adds the project's export paths to our map. We use this map to lookup
        a project based on its exports when we encounter an include in a source
        file. Export paths are case-insensitive. """

    # XXXblake On Unix, where external project paths tend to be "usr", this adds all sorts of junk
    # to the map
    for export in project.getExportPaths(deep=True, absPaths=False):
        if not export in exportMap:
            exportMap[export] = []
        # print "Adding ", export, " to project ", project.path XXXblake This reveals some bugs
        exportMap[export].append(project)
             
def getIncludes(source):

    """ Returns a list of relative, concrete include paths used by the specified (absolute) source. """

    includes = []

    # XXXblake We need to parse conditionals so we only process the right includes.
    # XXXblake Doesn't work for includes after the namespace (e.g. at the bottom of the file)
    # XXXblake Need to handle relative includes (e.g. #include "../foopy.h")
    for line in file(source):
        match = reInclude.match(line)
        if match:
            includes.append(match.group(1))
        elif reNamespace.match(line):
            break

    return includes

def getExportingProject(export):

    """ Returns the project that exports the supplied path. """

    exportDir = os.path.dirname(export)
    if not exportDir in exportMap:
        return None

    projects = exportMap[exportDir]
    exportingProject = None
    numProjects = len(projects)
    if numProjects > 1:
    
        # If we already determined the correct project for this export in the past, we cached it
        # in our map, so check for that first.
        if export in exportMap:
            exportingProject = exportMap[export]
        else:
            # If more than one project exports the given path, we need to determine
            # which one it is. We want to minimize cases like this (by using distinctive
            # export paths) since it slows down building.
            # XXXblake This assumes a header, but getLibs() also uses this function
            # to look up namespaced libraries. We should check the extension here and
            # look at export or lib paths accordingly. This will probably fail if, say,
            # two projects export "gecko" currently.
            for project in projects:
                absRealPath = project.getAbsolutePath(project.makeConcrete(export))
                if os.path.exists(absRealPath):
                    exportingProject = project
                    
                    # Add to our cache so future lookups are faster
                    exportMap[export] = exportingProject
                    break

    elif numProjects:
        exportingProject = projects[0]

    # Although we already have a project instance here, we call through load()
    # to ensure that the project is up to date.
    if exportingProject and isinstance(exportingProject, DevonProject):
        exportingProject = load(exportingProject.path)

    # Warn if a file includes a header that was marked for exclusion. This rare situation
    # arises if you try to prevent a project from building by excluding all the files in it
    # but fail to remove the associated includes. The linker usually complains anyways, but this
    # warning helps identify the source of the problem. Note that the correct way to prevent
    # a project from building is to exclude the project itself in its parent.
    if isinstance(exportingProject, DevonProject):
        path = exportingProject.getAbsolutePath(exportingProject.makeConcrete(export))
        if path in exportingProject.exclude:
            print "Warning: A header designated for exclusion was included (%s)" % path
    
    return exportingProject

def includeSource(root, name, isFile, types = []):

    """ Filters out project files, build and test directories, hidden directories,
        generated files, other platforms' files, and (optionally) files that aren't of the specified
        types. """

    # Filter hidden files and directories. This excludes things like the svn
    # working copy. # XXXblake Move under dir when dep files move.
    if name[0] == ".":
        return False
    
    if isFile:
        if types:
            index = name.rfind(".")
            if index == -1:
                return False
                
            ext = name[index+1:]
            if not ext in types:
                return False
    else:
                   
        # Filter other platforms' sources
        if sys.platform == "win32":
            if name == "mac" or name == "unix":
                return False
        elif sys.platform == "darwin":
            if name == "win":
                return False
        else:
            if name == "mac" or name == "win":
                return False

        # If the subdirectory is a built project of its own, don't crawl into
        # it since the files contained within are that project's sources, not
        # our own.
        if os.path.exists(os.path.join(root, name, projectFileName)):
            return False
            
        # Filter the build directory
        if name == "build":
            return False
        
    return True

def relativePath(fullPath, basePath):
    slash = basePath[-1] == "/" or basePath[-1] == "\\"
    return fullPath[len(basePath) + (not slash):]
    
def getSourcesIn(path, includeDirs = False, includeTests = False, absPaths = False, excludes = [],
    changedAfter = 0, types = []):       

    """ Returns the files in the specified path and its subfolders, excluding project files, build
        and test directories, etc. (see includeSource()). By default, the function returns paths
        relative to |path|; use absPaths to change that. You can also pass a list of absolute paths
        to exclude. """
        
    sources = []
    
    def getSource(root, name, changedAfter=changedAfter):                
        fullPath = os.path.join(root, name)
        
        source = None
        if not fullPath in excludes:
            if absPaths:
                source = fullPath
            else:
                source = relativePath(fullPath, path)

        if source:
            # We also check ctime below, which ensures that we count moved/copied files as "changed"
            # even though their modification times have not changed. (We can't *just* check ctime,
            # because on Windows it's only the creation time, although on Unix it encompasses both
            # modification and moves.
            if not changedAfter or os.path.getmtime(fullPath) > changedAfter \
                    or os.path.getctime(fullPath) > changedAfter:
                return source
            
    # Walk the directory tree looking for sources
    for root, dirs, files in os.walk(path):
    
        # Directories
        length = len(dirs)
        for i, dir in enumerate(reversed(dirs)):
           if not includeSource(root, dir, False) or (not includeTests and dir == "tests"):
                del dirs[length-i-1]
           elif includeDirs:
                # We don't exclude directories based on the mod date because their subdirectories
                # may have changed, so pass 0 here.
                source = getSource(root, dir, 0)
                if source:
                    sources.append(source)

        # Optimization: only bother checking files if the current directory mod time is newer than
        # our requested mod time
        if changedAfter and os.path.getmtime(root) < changedAfter:
            continue
            
        # Files
        for file in files:
            if not includeSource(root, file, True, types):
                continue

            source = getSource(root, file)
            if source:
                sources.append(source)
            
    return sources

def getPlatformAbbreviation():
    import sys
    if sys.platform == "win32":
        return "win"
    if sys.platform == "darwin":
        return "mac"
    return "unix"
