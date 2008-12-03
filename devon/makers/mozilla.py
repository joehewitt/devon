
import os.path, zipfile, glob, re, string, re
import devon.maker, devon.projects
import xul
from devon.tags import *

# **************************************************************************************************

defaultChromeDirs = ["content", "locale", "skin"]
ignoreFiles = [".DS_Store", ".svn", "tests"]

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

reXPIDL = re.compile(r"\.(idl)$")

reDomplate = re.compile("\$([_A-Za-z][_A-Za-z0-9.|]*)")
reDelim = re.compile("[\.\|]")
reProp = re.compile("[\s\{]_([_A-Za-z0-9]+):")
reDollar = re.compile("[\s\{](\$[_A-Za-z0-9]+):")

reEscaped = re.compile('(SS|INT|CI|CC)\("(.*?)"\)')
reEscaped1 = re.compile('(GET)\((.*?)\,\s*"(.*?)"\)')
reEscaped2 = re.compile('(CCSV|CCIN)\("(.*?)"\,\s*"(.*?)"\)')
reAll = re.compile(".")

rootFiles = ["chrome.manifest", "license.txt"]

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

scriptTag = """    <script type="application/x-javascript" src="%s"/>"""

# No obfuscator currently supported
obfuscatorCmd = None

# **************************************************************************************************

class FirefoxExtension(devon.maker.MakerManyToOne):
    def getTarget(self, project):
        return "%s.xpi" % project.name
        
    def needsUpdate(self, project, target):
        return True

    def build(self, project, out, sources, target):
        project.symbolMap = {}
        project.symbolCount = 0
        
        if os.path.exists(target):
            xpi = zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED)

            xpiDate = os.stat(target).st_mtime
            if needsRefresh(project, xpiDate):
                xpiDate = 0
        else:
            xpi = zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED)
            xpiDate = 0
            

        targetDirPath = os.path.dirname(target)
        componentsTargetDirPath = os.path.join(targetDirPath, "components")
        
        zipFiles(project, xpi, xpiDate, os.path.join(project.path, "install.rdf"), "install.rdf", out)
        zipFiles(project, xpi, xpiDate, os.path.join(project.path, "defaults"), "defaults", out)
        zipFiles(project, xpi, xpiDate, os.path.join(project.path, "icons"), "chrome/icons", out)
        zipFiles(project, xpi, xpiDate, componentsTargetDirPath, "components", out)
        zipFiles(project, xpi, xpiDate, os.path.join(project.path, "components"), "components", out, \
            processor=processChromeFile, pattern="*.js")
        buildChromeXPIJar(project, xpi, project.path, targetDirPath, "", out)
        buildPlatformChromeFiles(project, xpi, project.path, targetDirPath, out)
        
        xpi.close()
        
        return 0

    def install(self, project, out, sources, target):
        xpiPath = os.path.join(project.getBuildPath(), target)
        out << Block \
            << "Installing extension " << FileLink(path=xpiPath) << xpiPath << Close << Close
        
        if not project.config.firefoxProfile:
            out << "You must set variables.firefoxProfile to the path of your profile."
            return 1
        
        extPath = os.path.join(project.config.firefoxProfile, "extensions")

        if not os.path.exists(extPath):
            out << extPath << " does not exist."
            return 1
        
        extPath = os.path.join(extPath, project.config.extensionId)
        if not os.path.exists(extPath):
            os.mkdir(extPath)
            
        os.system("""unzip -o %s -d "%s" """ % (xpiPath, extPath))
        return 0

    def printAction(self, project, out, target):
        out << Block << "Updating XPI file " << FileLink(path=target) \
            << target << Close << "..." << Close

    def printResult(self, project, out, text):
        out << Block << text << Close

# **************************************************************************************************

class XPIDLCompile(devon.maker.Preprocessor):
    def getSourceTarget(self, project, source):
        if reXPIDL.search(source):
            return source
            
    def build(self, project, out, source, target):
        targetName, ext = os.path.splitext(target)
        targetDir = os.path.dirname(target)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
        
        gecko = devon.projects.getProjectByName("gecko")
        if gecko.defines.idlPath:
            xpidlDir = gecko.defines.idlPath
        else:
            xpidlDir = gecko.getAbsolutePath("idl")
        
        if not gecko.defines.skipIDLHeader:
            # XXXblake Kind of a hack...I think we need "one to many" preprocessors      
            line = "xpidl -m header -I%s -I. -o %s %s" % (xpidlDir, targetName, source)
            result = devon.make.executeCommand(project, self, line, out)
            if not result == 0:
                return result
            
        line = "xpidl -m typelib -I%s -o %s %s" % (xpidlDir, targetName, source)
        result = devon.make.executeCommand(project, self, line, out)

        return result

    def printAction(self, project, out, source, target):
        out << Block("progressBox progress-build") << "Compiling interface " \
            << FileLink(path=source) << source << Close \
            << "..." << Close << Flush

    def printResult(self, project, out, text):
        out << CodeBlock << text << Close

# **************************************************************************************************

def processChromeFile(path, targetPath, project):
    if not hasattr(project.config, "obfuscate") or not project.config.obfuscate:
        return True

    if hasattr(project.config, "obfuscated") \
            and (not os.path.basename(path) in project.config.obfuscated):
        return True

    name, ext = os.path.splitext(path)
    if ext == ".js":
        print "    Obfuscating..."
        js = obfuscateJS(path, targetPath, project)

        if hasattr(project, "xulScriptMap"):
            fileName = os.path.basename(path)
            if project.xulScriptMap.has_key(fileName):
                # Append the file to the aggregated script for each XUL file that imported it
                project.xulScriptMap[fileName] = js
                
                # Return none to prevent storing the file directly
                return None

        if hasattr(project.config, "scriptHeader"):
            js = project.config.scriptHeader + js

        return js
    elif ext == ".xul":
        return obfuscateXUL(path, targetPath, project)
    elif ext == ".xml":
        return obfuscateXBL(path, targetPath, project)
    else:
        return True

def obfuscateJS(path, targetPath, project, preprocess=True):
    if preprocess:
        localExcepPath = preprocessJS(path, project)
    else:
        localExcepPath = ""
        
    obfusPath = obfuscatorCmd % {}
        
    obfusLines = []
    for line in os.popen(obfusPath):
        obfusLines.append(line)

    if localExcepPath:
        os.remove(localExcepPath)
    
    obfusText = "".join(obfusLines)
    #f = open(path)
    #obfusText = f.read()
    #f.close()
    
    if preprocess:
        obfusText = postprocessJS(obfusText, path, project)

    return obfusText

def obfuscateXUL(path, targetPath, project):
    """Obfuscates XUL by aggregating all scripts and obfuscating inline event listeners."""
    
    f = open(path)
    txt = f.read()
    f.close()
        
    scriptAggIndex = -1
    scriptTags = []
    projectChromeDir = "chrome://%s/" % project.name

    # Iterate through all script tags in the document and replace
    # those which import from the project with a single import
    # to the aggregated script 
    scripts, scriptStart, scriptEnd = xul.iterateScripts(txt)
    for scriptPath in scripts:
        if scriptPath.find(projectChromeDir) == 0:
            scriptFileName = os.path.basename(scriptPath)
            if scriptAggIndex == -1:
                scriptAggIndex = project.xulFileCount
                project.xulFileCount += 1
                project.xulScripts[scriptAggIndex] = []
                project.xulScriptPaths[scriptAggIndex] = targetPath

            project.xulScriptMap[scriptFileName] = None
            project.xulScripts[scriptAggIndex].append(scriptFileName)

        else:
            scriptTags.append(scriptTag % scriptPath)
    
    # Replace the script tags
    if not scriptAggIndex == -1:
        scriptURI = projectChromeDir + "content/%s.js" % scriptAggIndex
        scriptTags.append(scriptTag % scriptURI)
        txt = "%s\n%s\n%s" % (txt[0:scriptStart], "\n".join(scriptTags), txt[scriptEnd:])
    
    newText = ""
    replaceIndex = 0
    
    # Loop thorugh all inline event listeners and obfuscate each
    tempPath = path+".tmp"
    for value, start, end in xul.iterateListeners(txt):
        fn = "function () {%s}\n" % value
        f = open(tempPath, "w")
        f.write(fn)
        f.close()
        
        print "Obfuscating %s..." % value
        obText = obfuscateJS(tempPath, "", project, preprocess=True)
        os.remove(tempPath)
        
        obName, obArgs, obBody = xul.parseFunction(obText)
        
        newText += txt[replaceIndex:start] + obBody
        replaceIndex = end
        
    newText += txt[replaceIndex:]

    return newText

def obfuscateXBL(path, targetPath, project):
    f = open(path)
    txt = f.read()
    f.close()
    
    newText = ""
    replaceIndex = 0
    
    # Loop through all members, obfuscate each, and then replace it
    tempPath = path+".tmp"
    for memberType, name, argNames, extra, body, start, end in xul.iterateMembers(txt):
        fn = "function %s(%s)\n{\n %s }\n" % (name, ", ".join(argNames), body)
        f = open(tempPath, "w")
        f.write(fn)
        f.close()
        
        print "Obfuscating %s %s..." % (memberType, name)
        obText = obfuscateJS(tempPath, "", project, preprocess=True)
        os.remove(tempPath)

        obName, obArgs, obBody = xul.parseFunction(obText)
        
        memberText = xul.restoreMember(memberType, obName, extra, obArgs, obBody)
        newText += txt[replaceIndex:start] + memberText
        replaceIndex = end
        
    newText += txt[replaceIndex:]

    return newText

# **************************************************************************************************
        
def preprocessJS(path, project):
    """Finds symbols defined in Domplates and creates a temorary local exceptions file
       where the obfuscator can find them.
       
       These parsers are very imprecise - beware, they might overstep their bounds"""
      
    f = open(path)
    txt = f.read()
    f.close()
    
    # Find all Domplate expressions in strings
    exceps = {}
    for expr in reDomplate.findall(txt):
        for excep in reDelim.split(expr):
            exceps[excep] = 1

    # Find all Domplate property arguments (like _foo:)
    for expr in reProp.findall(txt):
        exceps[expr] = 1
        exceps["_"+expr] = 1

    # Find all Domplate class arguments (like $foo:)
    for expr in reDollar.findall(txt):
        exceps[expr] = 1
    
    excepList = "\n".join(exceps.keys()) + "\n "

    localExcepPath = path+".tmp"
    f = open(localExcepPath, "w")
    f.write(excepList)
    f.close()
    
    return localExcepPath
    
def postprocessJS(txt, path, project):
    """Replaces all prefixed symbols with a short, unique name."""
    
    symbolMap = project.symbolMap
    localSymbolMap = {}
    
    prefix = project.config.obfuscatePrefix
    prefixLen = len(prefix)
    
    def repl(m):
        return """%s("%s")""" % (m.group(1), escape(m.group(2)))
    
    def repl1(m):
        return """%s(%s, "%s")""" % (m.group(1), m.group(2), escape(m.group(3)))

    def repl2(m):
        return """%s("%s", "%s")""" % (m.group(1), escape(m.group(2)), escape(m.group(3)))

    txt = re.sub(reEscaped, repl, txt)
    txt = re.sub(reEscaped1, repl1, txt)
    txt = re.sub(reEscaped2, repl2, txt)
    
    reSymbol = re.compile(project.config.obfuscatePrefix+"[_A-Za-z0-9\$]+")
    obSymbols = reSymbol.findall(txt)
    for obSymbol in obSymbols:
        symbol = obSymbol[prefixLen:]
        if not symbolMap.has_key(symbol):
            symbolMap[symbol] = encodeSymbol(project.symbolCount)
            project.symbolCount += 1

        localSymbolMap[symbol] = symbolMap[symbol]

    # Longer symbols need to be replaced first, because shorter ones
    # may be a subset of longer ones and replace them wrongly
    localSymbols = localSymbolMap.keys()
    localSymbols.sort(lambda a,b: len(b) - len(a))

    for symbol in localSymbols:
        obSymbol = prefix + symbol
        txt = txt.replace(obSymbol, symbolMap[symbol])
    
    return txt

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

def zipFile(project, zf, zipDate, sourcePath, zipPath, out, processor=None):
    out << Block << "Adding " << FileLink(path=sourcePath) << sourcePath << Close << Close

    fileDate = os.stat(sourcePath).st_mtime
    if fileDate > zipDate:
        if processor:
            text = processor(sourcePath, zipPath, project)
            if text == True:
                zf.write(sourcePath, zipPath)
            elif text:
                zf.writestr(zipPath, text)
        else:
            zf.write(sourcePath, zipPath)

def zipFiles(project, zf, zipDate, sourceDirPath, zipDirPath, out, processor=None, pattern=None):
    if os.path.isfile(sourceDirPath):
        zipFile(project, zf, zipDate, sourceDirPath, zipDirPath, out, processor)
    elif os.path.isdir(sourceDirPath):
        for name in getDirFiles(sourceDirPath, pattern):
            if name in ignoreFiles:
                continue
        
            sourcePath = os.path.join(sourceDirPath, name)
            zipPath = os.path.join(zipDirPath, name)
                    
            if os.path.isdir(sourcePath):
                zipFiles(project, zf, zipDate, sourcePath, zipPath, out, processor, pattern)
            else:
                zipFile(project, zf, zipDate, sourcePath, zipPath, out, processor)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

def buildChromeJar(project, jarName, sourceDirPath, targetDirPath, out, zip=None):
    project.xulScriptMap = {}
    project.xulScripts = {}
    project.xulScriptPaths = {}
    project.xulFileCount = 0

    jarDate = 0

    if zip:
        zipBasePath = targetDirPath
        chromeJar = zip
    else:
        if not os.path.exists(targetDirPath):
            os.makedirs(targetDirPath)

        zipBasePath = ""
        chromeJarPath = os.path.join(targetDirPath, jarName)
        jarExists = os.path.exists(chromeJarPath)
        chromeJar = zipfile.ZipFile(chromeJarPath, "w", zipfile.ZIP_DEFLATED)

        if jarExists:
            jarDate = os.stat(chromeJarPath).st_mtime
            if needsRefresh(project, jarDate):
                jarDate = 0
    
    chromeFiles = getChromeFiles(sourceDirPath, project)
    for chromePath in chromeFiles:
        chromeDirName = getChromeDirName(chromePath)
        if chromeDirName:
            zipPath = os.path.join(zipBasePath, chromeDirName)
            zipFiles(project, chromeJar, jarDate, chromePath, zipPath, out, \
                processor=processChromeFile)

    # Store all of the aggregated XUL scripts
    for i in xrange(0, project.xulFileCount):
        path = project.xulScriptPaths[i]
        newPath = os.path.join(os.path.dirname(path), "%s.js" % i)
        
        # Create the aggregated script in the order that each was imported in XUL
        scripts = []
        
        # Put the project-defined script header atop the file if one is defined
        if hasattr(project.config, "scriptHeader"):
            scripts.append(project.config.scriptHeader)
            
        for scriptFileName in project.xulScripts[i]:
            if project.xulScriptMap.has_key(scriptFileName):
                script = project.xulScriptMap[scriptFileName].rstrip()
                scripts.append(script)
            else:
                print "WARNING: %s was imported but does not exist." % scriptFileName
            
        chromeJar.writestr(newPath, "".join(scripts))

    if not zip:
        chromeJar.close()
        return chromeJarPath

def buildChromeXPIJar(project, xpi, sourceDirPath, targetDirPath, xpiPath, out):
    for rootFileName in rootFiles:
        manifestPath = os.path.join(sourceDirPath, rootFileName)
        if os.path.isfile(manifestPath):
            manifestXPIPath = os.path.join(xpiPath, rootFileName)
            xpi.write(manifestPath, manifestXPIPath)

    if hasattr(project.config, "chromeJar") and not project.config.chromeJar:
        chromeXPIPath = os.path.join(xpiPath, "chrome", project.name)
        buildChromeJar(project, "", sourceDirPath, chromeXPIPath, out, zip=xpi)
    else:
        jarName = "%s.jar" % project.name
        chromeJarPath = buildChromeJar(project, jarName, sourceDirPath, targetDirPath, out)
        chromeJarXPIPath = os.path.join(xpiPath, "chrome", jarName)

        out << Block << "Building jar " << FileLink(path=chromeJarPath) << chromeJarPath \
            << Close << Close
        xpi.write(chromeJarPath, chromeJarXPIPath)

def buildPlatformChromeFiles(project, xpi, sourceDirPath, targetDirPath, out):
    platformPath = os.path.join(sourceDirPath, "platform")
    if os.path.isdir(platformPath):
        for platformName in os.listdir(platformPath):
            if not platformName in ignoreFiles:
                platformDirPath = os.path.join(platformPath, platformName)
                if os.path.isdir(platformDirPath):
                    platformTargetDirPath = os.path.join(targetDirPath, platformName)
                    platformXPIPath = os.path.join("platform", platformName)
                    buildChromeXPIJar(project, xpi, platformDirPath, platformTargetDirPath, \
                        platformXPIPath, out)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

def getChromeDirName(source):
    parts = source.split(os.sep)
    for name in defaultChromeDirs:
        if name in parts:
            index = parts.index(name)
            return os.sep.join(parts[index:])
    
def getChromeFiles(path, project):
    paths = []

    if hasattr(project.config, "chromeDirs"):
        dirs = project.config.chromeDirs
    else:
        dirs = defaultChromeDirs
        
    for name in dirs:
        chromePath = os.path.join(path, name)
        if os.path.isdir(chromePath):
            paths.append(chromePath)
    
    return paths

def getDirFiles(dirPath, pattern=None):
    if pattern:
        for path in glob.glob(os.path.join(dirPath, pattern)):
            yield os.path.basename(path)
    else:
        def sortScriptsLast(a,b):
            if os.path.splitext(a)[1] == ".js":
                return 1
            else:
                return -1
            
        paths = os.listdir(dirPath)
        
        # Sort scripts to the end because we need to process XUL first
        paths.sort(sortScriptsLast)

        for path in paths:
            yield path

def needsRefresh(project, zipDate):
    # XXXjoe Zip rebuilding not working yet
    return True

    if project.config.OBFUS_EXCEPTIONS and os.path.exists(project.config.OBFUS_EXCEPTIONS):
        exceptionsDate = os.stat(project.config.OBFUS_EXCEPTIONS).st_mtime
        return exceptionsDate > zipDate

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
# Symbol encoding - uses base 63, the set of legal JavaScript symbol characters (except $)

NOTATION = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
NOTATION_BASE = len(NOTATION)

def encodeSymbol(index):
    return "_%s$" % encodeNumber(index)

def encodeNumber(index):
    nums = getBaseNumbers(index)
    nums.reverse()
    return ''.join([NOTATION[n] for n in nums])

def getBaseNumbers(n):
    converted = []
    quotient, remainder = divmod(n, NOTATION_BASE)
    converted.append(remainder)
    if quotient != 0:
        converted.extend(getBaseNumbers(quotient))
    return converted

def escape(text):
    return re.sub(reAll, lambda (m): "%%%x" % ord(m.group(0)), text)
