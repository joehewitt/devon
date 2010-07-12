
from devon.tags import *
import devon.projects, devon.maker, devon.spawn, devon.stream
import datetime, os.path, shutil, sys, time, traceback

# **************************************************************************************************

global cancelBuild
cancelBuild = False

defaultAction = "build"

# **************************************************************************************************

def make(projectPath=None, action=None, out=None, config=None, resetDeps=True):
    """ Carries out the specified action for the specified project. We maintain
        a global list of built projects during a build session so we don't waste
        time re-checking them for updates. resetDeps is used internally to track
        whether or not it's time to reset that list (i.e. a make has completed),
        so we don't reset it each time we make a child.
    """
    global cancelBuild, allDeps
    cancelBuild = False
    
    # XXXjoe Don't think we need sessions anymore but I'll leave it for now
    session = devon.projects.getSession()    

    result = 0

    if isinstance(projectPath, devon.projects.Project):
        project = projectPath
    else:
        if not projectPath:
            projectPath = os.getcwd()
        if not action:
            action = defaultAction
        if not out:
            out = devon.stream.OutStream(sys.stdout)

        project = devon.projects.load(projectPath)
        if not project:
            raise Exception("%s is not a buildable project " % projectPath)
            
    for child in project.getChildProjects():
        result = make(child.path, action, out, resetDeps=False)
        if not result == 0:
            allDeps = []
            return result
    
    # Make sure the working directory is the project path so that all relative paths work
    cwd = os.getcwd()
    os.chdir(project.path)

    try:
        c1 = time.time()
        
        if action == "build":
            result = build(project, out)
        elif action == "buildTests":
            result = buildTests(project, out)
        elif action == "install":
            result = install(project, out)
        elif action == "clean":
            result = clean(project, out)
        else:
            raise Exception("The action '%s' is not recognized" % action)
        
        print "Total time for %s: %f" % (action, time.time()-c1)
    
    except StopBuildException:
        out << Block("resultBox result-cancelled") << "Cancelled." << Close
        result = -1        

    except:
        exc = sys.exc_info()
        traceback.print_exception(*exc)
        out << Block("traceback") << str(exc[0]) << str(exc[1]) << Close
        result = -1

    os.chdir(cwd)
    
    if resetDeps:
        allDeps = []
    
    return result

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def build(project, out):
    out << Header(level=2) << "Project " \
        << FileLink(path=project.path) << project.path << Close \
        << "..." << Close << Flush

    sources = project.getSources()
    sources = sortSources(sources)    
        
    result = buildStep(project, out, project.buildPre, sources)
    if result == 0:
        result = buildStep(project, out, project.build, sources)
        if result == 0:
            result = buildStep(project, out, project.buildPost, sources)
            if not result == 0:
                return result
                        
    session = devon.projects.getSession()    
    if not project.debug:
        if project.distInstallPaths:
            installPaths(project, project.distInstallPaths, out)
         
        result = buildStep(project, out, project.dist, sources)

    return result

def buildStep(project, out, makers, sources, deps = None):
    if isinstance(makers, tuple) or isinstance(makers, list):
        for maker in makers:
            targets = buildMakerChain(project, out, maker, sources)
            if targets == -1:
                return -1

    elif isinstance(makers, devon.maker.Maker):
        targets = buildMakerChain(project, out, makers, sources)
        if targets == -1:
            return -1
        
    return 0
    
def buildMakerChain(project, out, maker, sources):
    targets = sources                

    while maker.previousMaker:
        maker = maker.previousMaker

    while maker:
        targets = buildMaker(project, out, maker, targets)
        if targets == -1:
            return -1

        maker = maker.nextMaker

    return targets

allDeps = []

def buildMaker(project, out, maker, sources):
    global cancelBuild
    if cancelBuild:
        raise StopBuildException()

    sources = maker.filterSources(project, sources)
    targets = []
    if isinstance(maker, devon.maker.Preprocessor):
        for source in sources:
            if cancelBuild:
                raise StopBuildException()

            target = maker.getSourceTarget(project, source)
            if not target:
                targets.append(source)
            else:
            
                target = project.getBuildPath(target)
                              
                targets.append(target)

                if targetNeedsUpdate(source, target) \
                        or maker.needsUpdate(project, source, target):
                    maker.printAction(project, out, source, target)
    
                    status = maker.build(project, out, source, target)                    
                    if status > 0:
                        return -1

    elif isinstance(maker, devon.maker.MakerOneToOne):
        for source in sources:
            if cancelBuild:
                raise StopBuildException()

            target = maker.getSourceTarget(project, source)
            if not target:
                continue
                
            if source == project.pch:
                target = project.getAbsolutePath(target)
            else:
                target = project.getBuildPath(target)
                
            targets.append(target)
            
            targetDir = os.path.dirname(target)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)

            if targetNeedsUpdate(source, target) \
                    or maker.needsUpdate(project, source, target):
                maker.printAction(project, out, source, target)

                status = maker.build(project, out, source, target)                
                if status > 0:
                    return -1
    
    elif isinstance(maker, devon.maker.MakerManyToOne):
        target = maker.getTarget(project)
        if not target:
            return
                      
        target = project.getBuildPath(target)
        targets.append(target)

        targetDir = os.path.dirname(target)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)

        needUpdate = maker.needsUpdate(project, target)
        if not needUpdate:
            projectPath = os.path.join(project.path, devon.projects.projectFileName)
            if targetNeedsUpdate(projectPath, target):
                needUpdate = True   
            else:
                for source in sources:
                    if targetNeedsUpdate(source, target):
                        needUpdate = True
                        break

        global allDeps
        allDeps.append(project)
        
        # Before we build the project, ensure that its dependencies are up to date
        # XXXblake We could probably speed all this up quite a bit if we cached
        # certain things on the build session, such as the project's dependency list.
        for dep in maker.getDependencies(project):
            if isinstance(dep, devon.projects.DevonProject) and not dep in allDeps:
                allDeps.append(dep)
                
                cwd = os.getcwd()
                os.chdir(dep.path)
                result = build(dep, out)
                if not result == 0:
                    return result
                os.chdir(cwd)

            if not needUpdate:
                depTarget = dep.getBuildTarget()
                if depTarget and targetNeedsUpdate(depTarget, target):
                    needUpdate = True

        if needUpdate:
            maker.printAction(project, out, target)

            status = maker.build(project, out, sources, target)            
            if status > 0:
                return -1
    
    elif isinstance(maker, devon.maker.MakerOneToMany):
        for source in sources:
            if cancelBuild:
                raise StopBuildException()

            sourceTargets = maker.getSourceTargets(project, source)
            if not sourceTargets:
                continue
                
            for target in sourceTargets:
                target = project.getBuildPath(target)
                targets.append(target)
            
            targetDir = os.path.dirname(target)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)
            
            if targetNeedsUpdate(source, target) or maker.needsUpdate(project, source, target):
                maker.printAction(project, out, source, sourceTargets)

                status = maker.build(project, out, source, target)
                
                if status > 0:
                    return -1

    return targets

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def buildTests(project, out):
    out << Header(level=2) << "Tests for Project " \
        << FileLink(path=project.path) << project.path << Close \
        << "..." << Close << Flush
       
    sources = project.getSources()
    sources = sortSources(sources)    
    
    return buildStep(project, out, project.buildTests, sources)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def clean(project, out):
    out << Header(level=2) << "Project " \
        << FileLink(path=project.path) << project.path << Close \
        << "..." << Close << Flush

    sources = project.getSources()

    result = cleanStep(project, out, project.buildPre, sources)
    if result == 0:
        result = cleanStep(project, out, project.build, sources)
        if result == 0:
            result = cleanStep(project, out, project.buildPost, sources)
    
    return 0

def cleanStep(project, out, makers, sources):
    if isinstance(makers, tuple) or isinstance(makers, list):
        for maker in makers:
            cleanMakerChain(project, out, maker, sources)

    elif isinstance(makers, devon.maker.Maker):
        cleanMakerChain(project, out, makers, sources)

    return 0
    
def cleanMakerChain(project, out, maker, sources):
    targets = sources

    while maker.previousMaker:
        maker = maker.previousMaker

    while maker:
        targets = cleanMaker(project, out, maker, targets)
        if targets == None:
            break

        maker = maker.nextMaker
    
    return targets
    
def cleanMaker(project, out, maker, sources):
    global cancelBuild
    if cancelBuild:
        raise StopBuildException()

    sources = maker.filterSources(project, sources)
    targets = []

    if isinstance(maker, devon.maker.Preprocessor):
        for source in sources:
            if cancelBuild:
                raise StopBuildException()

            target = maker.getSourceTarget(project, source)
            if not target:
                targets.append(source)
            else:                
                targets.append(target)

                target = os.path.join(project.path, target)
                deleteTarget(target, out)

    elif isinstance(maker, devon.maker.MakerOneToOne):
        for source in sources:
            if cancelBuild:
                raise StopBuildException()
                
            target = maker.getSourceTarget(project, source)
            if not target:
                continue
                
            if source == project.pch:
                target = os.path.join(project.path, target)
            else:
                target = project.getBuildPath(target)

            targets.append(target)
            deleteTarget(target, out)
    
    elif isinstance(maker, devon.maker.MakerManyToOne):
        target = maker.getTarget(project)
        if not target:
            return
            
        target = project.getBuildPath(target)
        targets.append(target)
        deleteTarget(target, out)
    
    elif isinstance(maker, devon.maker.MakerOneToMany):
        for source in sources:
            if cancelBuild:
                raise StopBuildException()
                
            sourceTargets = maker.getSourceTargets(project, source)
            if not sourceTargets:
                continue
            
            for target in sourceTargets:   
                target = project.getBuildPath(target)
                targets.append(target)
                deleteTarget(target, out)

    return targets

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def install(project, out):
    out << Header(level=2) << "Project " \
        << FileLink(path=project.path) << project.path << Close \
        << "..." << Close << Flush

    if project.installPaths:
        installPaths(project, project.installPaths, out)

    result = 0
    
    if project.build:
        if isinstance(project.build, devon.maker.MakerOneToOne):
            for source in project.getSources(includeDirs=True):
                target = project.build.getSourceTarget(project, source)
                result = project.build.install(project, out, source, target)
                if not result == 0:
                    break
                    
        elif isinstance(project.build, devon.maker.MakerManyToOne):
            target = project.build.getTarget(project)
            if target:
                result = project.build.install(project, out, project.getSources(includeDirs=True), target)

    return result

def installPaths(project, paths, out):
    for destPath in paths:
        sources = []
        source = paths[destPath]
        
        if isinstance(source, tuple) or isinstance(source, list):
            expandedPaths = [project.expandString(path) for path in source]
            sources += project.getPathList(expandedPaths)
        else:
            expandedPath = project.expandString(source)
            sources += project.getPathList((expandedPath,))

        fullDestPath = project.expandString(destPath)

        for sourcePath in sources:
            try:
                installFile(project, out, sourcePath, fullDestPath)
            except:
                result = 1
                break
        
def installFile(project, out, sourcePath, destPath):    
    if not os.path.exists(destPath):
        os.makedirs(destPath)
    
    resultPath = os.path.join(destPath, os.path.basename(sourcePath))
    
    out << Block("progressBox progress-install") << "Installing " \
        << FileLink(path=resultPath) << resultPath << Close \
        << "..." << Close << Flush

    copyFile(sourcePath, destPath) 

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def targetNeedsUpdate(source, target):
    return not os.path.exists(target) or not os.path.exists(source) \
        or os.path.getmtime(source) > os.path.getmtime(target)

def deleteTarget(target, out):
    if os.path.exists(target):
        out << Block("progressBox progress-clean") << "Removing " \
            << FileLink(path=target) << target << Close \
            << "..." << Close << Flush

        if os.path.isdir(target):
            shutil.rmtree(target)        
        else:
            os.remove(target)
    
def copyFile(source, destDir):
    if not source or not destDir:
        return
        
    if os.path.isdir(source):
        newDest = os.path.join(destDir, os.path.basename(source))
        if not os.path.exists(newDest):
            print "cp -R '%s' '%s'" % (source, newDest)
            os.system("cp -R '%s' '%s'" % (source, newDest))
    else:
        destPath = os.path.join(destDir, os.path.basename(source))
        if os.path.exists(destPath):
            sourceTime = datetime.datetime.fromtimestamp(os.stat(source).st_mtime)
            destTime = datetime.datetime.fromtimestamp(os.stat(destPath).st_mtime)
            if sourceTime > destTime:
                os.system("cp '%s' '%s'" % (source, destDir))
        else:                    
            os.system("cp '%s' '%s'" % (source, destDir))

def executeCommand(project, maker, command, out):
    if project.showCommands:
        out << CodeBlock << command << Close << Flush

    try:        
        child = devon.spawn.Spawn(command)
    except:
        raise Exception("Unable to launch executable '%s'" % command.split(" ")[0])
        
    text = ""
    while child.isalive():
        text += child.read()

    text += child.read()
    
    if text:
        maker.printResult(project, out, text)
    
    return child.exitStatus

def sortSources(sources):
    """Sort the sources by last modification time so we first build the files you touched most
       recently, with the precompiled header first in the list."""

    pchSource = devon.projects.pchH
    if sys.platform == "win32":
        pchSource = pchSource.replace(".h", ".cpp")
        
    pchFound = None
    pchLen = len(pchSource)
    sorted = []
    for source in sources:
        if source[-pchLen:] == pchSource:
            pchFound = source
        else:        
            modTime = os.path.getmtime(source)
            sorted.append((modTime, source))

    sorted.sort(reverse=True)
    sources = [pair[1] for pair in sorted]
    
    if pchFound:
        sources.insert(0, pchFound);

    return sources

# **************************************************************************************************

class StopBuildException(Exception):
    pass
