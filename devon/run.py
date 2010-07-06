
import devon.log, devon.jump, devon.test
import devon.makers.python, devon.makers.link

import devon.stream
from devon.tags import *

import os.path, sys, types

# **************************************************************************************************

disabledLogsFilePath = devon.log.getLogPath("DevonDisabledLogs.txt")
catalogInputFilePath = devon.log.getLogPath("DevonTestCatalogInput.txt")
catalogOutputFilePath = devon.log.getLogPath("DevonTestCatalogOutput.txt")

# **************************************************************************************************
# Local Helpers

# Wraps arguments with spaces in quotes on Windows. No-op on other platforms.
def wrapArgs(args):
    if sys.platform == "win32":
        for i in range(len(args)):
            if (args[i].find(" ") != -1):
                args[i] = "\"%s\"" % args[i]
    
    return args

# **************************************************************************************************

def runProjectExecutable(project, exeName=None, disabledLogs=None, debugger=False, out=None):
    if not out:
        out = devon.stream.OutStream(sys.stdout)

    if disabledLogs:
        writeDisabledLogs(project, disabledLogs)
        
    handler = TestPrintHandler(project, out)

    if not exeName:
        if project.defaultProject:
            defaultProject = project.getChildProject(project.defaultProject)
            if defaultProject:
                exeName = defaultProject.getBuildTarget()
    
    if exeName:
        out << Header(level=1) << "Running '%s'..." % os.path.basename(exeName) << Close << Flush
        
        runCommand(exeName, [], handler, project, debugger, out)

        if not handler.exitSucceeded:
            out << Block("resultBox result-crash") << "Program crashed!" << Close
        elif handler.testErrorCount == 0:
            out << Block("resultBox result-success") << "Success" << Close
        else:
            out << Block("resultBox result-failure") << "Errors occurred" << Close

def runProjectPython(project, exeName=None, disabledLogs=None, debugger=False, out=None):
    if not out:
        out = devon.stream.OutStream(sys.stdout)

    if disabledLogs:
        writeDisabledLogs(project, disabledLogs)
        
    if exeName:
        out << Header(level=1) << "Running '%s'..." % exeName << Close << Flush
        
        runner = PythonTestRunner(project)
        success = runner.run(exeName, debugger, out)

        if not success:
            out << Block("resultBox result-crash") << "Program crashed!" << Close
        else:
            out << Block("resultBox result-success") << "Success" << Close
        
def runProjectTests(project, targetName, disabledLogs, debugger, out):
    if disabledLogs:
        writeDisabledLogs(project, disabledLogs)

    out << Header(level=1) << "Running Tests..." << Close << Flush

    testRunners = getProjectTestRunners(project)

    if targetName:
        targetNames = targetName.split("/")
        targetNameRoot = targetNames[0]
        targetNameBase = "/".join(targetNames[1:])
        
        # Reduce the list to only the runner that matches the targetName
        testRunners = [runner for runner in testRunners \
            if pathToTestId(runner.project.path) == targetNameRoot]
    else:
        targetNameBase = ""
        
    testErrorCount = 0
    exitSucceeded = True
    
    for testRunner in testRunners:
        testErrorCount, exitSucceeded = testRunner.runTests(out, targetNameBase, debugger)
        
    if not exitSucceeded:
        out << Block("resultBox result-crash") << "Program crashed!" << Close
    elif testErrorCount == 0:
        out << Block("resultBox result-success") << "Success" << Close
    else:
        out << Block("resultBox result-failure") << "Errors occurred" << Close

def writeProjectCatalog(project, out):
    def writeProject(project, out, alwaysWrite=False):
        
        # A project should only be written if it's buildable, and a project is only buildable if it
        # itself is buildable or if any of its children (recursively) are buildable.
        # XXXblake This is slow because we pre-calculate all child projects. It would be faster if
        # getChildProjects() was a generator, or if it cached the children.
        if not alwaysWrite:
            alwaysWrite = project.build is not None
            if not alwaysWrite:
                for childProject in project.getChildProjects(True):
                    if childProject.build:
                        alwaysWrite = True
                        break
            
        for childProject in project.getChildProjects(False):
            shouldWrite = alwaysWrite or childProject.dist
                
            if shouldWrite:
                title = os.path.basename(childProject.path)
                path = childProject.path.replace("\\", "/")
                out << '{name: "%s", itemType: "Project", id: "%s", keepId: true, children: [\n' \
                    % (title, path)
            
            writeProject(childProject, out)

            if shouldWrite:
                out << ']},\n' << Flush

    out << '['
    writeProject(project, out, True)
    out << ']\n'

def writeProjectLogCatalog(project, out):
    out << "[\n"

    testRunners = getProjectTestRunners(project)
    for testRunner in testRunners:
        testRunner.writeLogCatalog(out)

    out << "]\n"

def writeProjectTestCatalog(project, out):
    out << "[\n"
    
    writeProjectExecutablePaths(project, out)

    testRunners = getProjectTestRunners(project)
    for testRunner in testRunners:
        testRunner.writeTestCatalog(out)
        
    out << "]\n"

# **************************************************************************************************

def writeDisabledLogs(project, disabledLogs):
    # XXX This really should only write out the log names for just the project that
    #     we are about to execute, but for now we only have a flat list of all log names
    
    for childProject in project.getChildProjects():
        if isinstance(childProject.build, devon.makers.link.Link):
            linkCommand = devon.makers.link.LinkTestRunner()
            commandName = linkCommand.getTarget(childProject)
            buildPath = childProject.getBuildPath(commandName)
            #logsFilePath = os.path.join(os.path.dirname(buildPath), logsFileName)
            
            logsFile = file(disabledLogsFilePath, "w")
            for logName in disabledLogs:
                logsFile.write(logName + "\n")
            logsFile.close()

def writeProjectExecutablePaths(project, out):
    for childProject in project.getChildProjects():
        if isinstance(childProject.build, devon.makers.link.LinkExecutable):
            commandPath = childProject.getBuildTarget()
            if commandPath:
                name = os.path.basename(commandPath)
                handler = TestCatalogPrintHandler(childProject, out)
                handler.declareTest("%s" % childProject.name, id="")
                handler.declareTest(name, id="exe:%s" % commandPath)
                handler.endDeclareTest()
                handler.endDeclareTest()
        elif isinstance(childProject.build, devon.makers.python.PythonModules):
            handler = TestCatalogPrintHandler(childProject, out)
            handler.declareTest("%s" % childProject.name, id="")
            for name in childProject.pythonExes:
                handler.declareTest(name, id="py:%s" % name, testType=devon.test.ExeType)
                handler.endDeclareTest()
            handler.endDeclareTest()
            
        writeProjectExecutablePaths(childProject, out)

def getProjectTestRunners(project, testRunners=None):
    if not testRunners:
        testRunners = []
    
    if isinstance(project.build, devon.makers.link.Link):
        testRunner = ExeTestRunner(project)
        testRunners.append(testRunner)

    elif isinstance(project.build, devon.makers.python.PythonModules):
        testRunner = PythonTestRunner(project)
        testRunners.append(testRunner)

    # Recursively get test runners from our children
    for childProject in project.getChildProjects():
        testRunners = getProjectTestRunners(childProject, testRunners)

    return testRunners

def runCommand(commandPath, args, handler, project, debugger, out):
    pyEnv = initPythonEnvironment(project)
        
    print ">>> %s %s" % (commandPath, " ".join(args))

    reader = devon.log.LogReader(commandPath, args, debugger=debugger)
    if not reader.pid:
        return
    
    out << Script << ("parent.runBegin(%d);" % reader.pid) << Close

    reader.process(handler)

    out << Script << ("parent.runEnd(%d);" % reader.pid) << Close

    restorePythonEnvironment(pyEnv)

# **************************************************************************************************

def initPythonEnvironment(project):
    if sys.platform == "win32":
        delim = ";"
        prevPyPath = os.getenv("PYTHONPATH") or ""
    else:
        delim = ":"

        # XXXjoe Might need to do this if you want to use the bash PYTHONPATH
        #prevPyPath = os.popen("source ~/.bash_profile; %s -c \"import sys; print ':'.join(sys.path)\"" % getPythonPath(project)).read().strip()
        
        # XXXjoe Might need to do this if you want to extend the current PYTHONPATH
        prevPyPath = os.getenv("PYTHONPATH") or ""
        
        prevPyPath = ""

    pyPath = prevPyPath
    
    for path in [".."] + project.pythonPaths:
        expandedPath = project.expandString(path)
        absPath = os.path.abspath(os.path.join(project.path, expandedPath))
        pyPath += "%s%s" % (delim, absPath)
    
    print ">>> export PYTHONPATH=%s" % pyPath
    os.putenv("PYTHONPATH", pyPath)

    return prevPyPath
    
def restorePythonEnvironment(prevPyPath):
    os.putenv("PYTHONPATH", prevPyPath)

def getPythonPath(project):
    if hasattr(project.config, "pythonBin"):
        pythonPath = pythonPathDebug = project.config.pythonBin
    elif sys.platform == "win32":
        pythonPath = "c:/program files/python25/python.exe"
        pythonPathDebug = "c:/program files/python25/python_d.exe"
    else:
        pythonPath = "/usr/bin/python"
        pythonPathDebug = "/usr/bin/python" # XXXjoe No debug builds for me yet

    # If we're running tests in debug mode, use the debug version of Python, which will
    # automatically use the debug versions of any extensions
    if devon.projects.getSession().debug:
        return pythonPathDebug
    
    return pythonPath        
            
class ExeTestRunner:
    def __init__(self, project):
        self.project = project

    def getCommandPath(self):
        linkCommand = devon.makers.link.LinkTestRunner()
        commandName = linkCommand.getTarget(self.project)
        buildPath = self.project.getBuildPath(commandName)
        
        return buildPath
        
    def writeLogCatalog(self, out):
        commandPath = self.getCommandPath()
        args = ["--mode", "logCatalog"]
        
        if not os.path.exists(commandPath):
            return

        reader = devon.log.LogReader(commandPath, args)
        if not reader.pid:
            return
    
        handler = LogCatalogPrintHandler(self.project, out)
        
        projectName = getProjectTargetName(self.project)
        handler.declareProject(projectName)
        
        reader.process(handler)

    def writeTestCatalog(self, out):
        commandPath = self.getCommandPath()
        if not os.path.exists(commandPath):
            return
            
        args = ["--mode", "testCatalog"]
        
        reader = devon.log.LogReader(commandPath, args, log=catalogOutputFilePath)
        if not reader.pid:
            return
    
        handler = TestCatalogPrintHandler(self.project, out)
        reader.process(handler)

    def runTests(self, out, targetName, debugger=False):
        commandPath = self.getCommandPath()
        handler = TestPrintHandler(self.project, out)

        projectId = pathToTestId(self.project.path)
        handler.beginTest(projectId)
        
        args = []
        if targetName:
            args += ["--target", targetName]
    
        runCommand(commandPath, args, handler, self.project, debugger, out)

        if not handler.exitSucceeded:
            out << Script << 'testExceptionThrown()' << Close
            
        handler.endTest()

        return handler.testErrorCount, handler.exitSucceeded
        
    def run(self, out):
        pass
    
# **************************************************************************************************

class PythonTestRunner(ExeTestRunner):
    def writeLogCatalog(self, out):
        pass
        
    def writeTestCatalog(self, out):
        pyEnv = initPythonEnvironment(self.project)
                   
        moduleName = getProjectTestModule(self.project)
        
        args = wrapArgs(["-c", "import devon.test; devon.test.writeTestCatalog('%s')" % moduleName])
       
        # If the catalog fails to load, uncomment  this to debug it on Mac
        #command = "gdb --args %s %s %s" \
        #    % (getPythonPath(self.project), args[0], "\"%s\"" % args[1])
        #os.system(command)
        
        print ">>> %s %s" % (getPythonPath(self.project), " ".join(args))
        reader = devon.log.LogReader(getPythonPath(self.project), args, log=catalogOutputFilePath)
        if not reader.pid:
            return
    
        handler = TestCatalogPrintHandler(self.project, out)
        reader.process(handler)

        restorePythonEnvironment(pyEnv)
        
    def runTests(self, out, targetName, debugger=False):
        pyEnv = initPythonEnvironment(self.project)

        if targetName == "Tests":
            targetName = getProjectTestModule(self.project)
            
        handler = TestPrintHandler(self.project, out)

        projectId = pathToTestId(self.project.path)
        handler.beginTest(projectId)

        args = wrapArgs(["-c", "import devon.test; devon.test.runTests('%s')" \
            % targetName])
        print ">>> %s %s" % (getPythonPath(self.project), " ".join(args))
        reader = devon.log.LogReader(getPythonPath(self.project), args, debugger=debugger)
        if not reader.pid:
            return
    
        reader.process(handler)

        handler.endTest()

        restorePythonEnvironment(pyEnv)
        
        return handler.testErrorCount, handler.exitSucceeded
        
    def run(self, name, debugger, out):
        exeName, args = self.project.pythonExes[name]
        
        argValues = []
        for value in args:
            if type(value) == str:
                value = "'%s'" % value.replace("'", "\\'")
            else:
                value = str(value)

            argValues.append(value)
            
        # XXXjoe Once upon a time I used this to specify args indirectly through
        # project variable lookups, but now we just pass the arg values literally
        # for name in argNames:
        #     if hasattr(self.project.config, name):
        #         testArg = getattr(self.project.config, name)
        #         if type(testArg) == str:
        #             testArg = "'%s'" % testArg.replace("'", "\\'")
        #         else:
        #             testArg = str(testArg)
        #         argValues.append(testArg)
        #     else:
        #         argValues.append("None")
        
        testArgs = ",".join(argValues)
        
        handler = TestPrintHandler(self.project, out)

        args = wrapArgs(["-c", "import devon.test; devon.test.runExe('%s',%s)" \
            % (exeName, testArgs)])
        
        runCommand(getPythonPath(self.project), args, handler, self.project, debugger, out)
        
        return handler.exitSucceeded
                
# **************************************************************************************************

class LogCatalogPrintHandler:
    def __init__(self, project, out):
        self.project = project
        self.out = out
        
    def write(self, text):
        pass

    def close(self):
        pass

    def flush(self):
        pass
    
    def declareProject(self, name):
        self.out << '{name: "%s", type: "project"},' % (name) << Flush

    def declareCategory(self, name, disabled):
        self.out << '{name: "%s", disabled: %s, type: "category"},' % (name, disabled) << Flush

# **************************************************************************************************

class TestCatalogPrintHandler:
    def __init__(self, project, out):
        self.project = project
        self.out = out
        self.testStackCount = 0
        self.rootInfo = None
        
    def write(self, text):
        pass

    def close(self):
        pass

    def flush(self):
        pass
    
    def declareTest(self, name, testType=0, testStatus="", id=None):
        self.testStackCount += 1

        testTypeName = devon.test.testTypeNames[int(testType)]
        
        if id == None:
            id = name

        if id == "Tests":
            projectName = getProjectTargetName(self.project)
            name = projectName
                
        if self.testStackCount == 1:
            projectId = pathToTestId(self.project.path)
            id = "/".join((projectId, id))

            # Save the name/id of the root header for later, when the first child is added
            self.rootInfo = (name, id, testTypeName)
        else:
            if name.find("Tests") == len(name) - 5:
                name = name[0:-5]
            elif name.find("test") == 0:
                name = name[4:]
            elif name.find("Test") == 0:
                name = name[4:]
            
            if self.rootInfo:
                # Only write the root header when the first child is added
                self.out << ('{name: "%s", id: "%s", itemType: "%s", children: [\n' \
                    % self.rootInfo) << Flush
                self.rootInfo = None
            
            self.out << '{name: "%s", id: "%s", itemType: "%s", testStatus: "%s", children: [\n' \
                % (name, id, testTypeName, testStatus) << Flush

    def endDeclareTest(self):
        self.testStackCount -= 1
        
        if self.testStackCount == 0:
            # Only close the root header if it was ever opened
            if not self.rootInfo:
                self.out << ']},\n' << Flush
        else:
            self.out << ']},\n' << Flush

# **************************************************************************************************

class TestPrintHandler:
    uniqueId = 0
    
    def __init__(self, project, out):
        self.project = project
        self.out = out
        self.testStack = []
        self.loggedStack = []
        self.inText = False
        self.inBlock = 0
        
        self.testErrorCount = 0
        self.exitSucceeded = False
        
    def __getUniqueId(self):
        self.uniqueId += 1
        return self.uniqueId
    
    def checkLooseEnds(self):
        self.checkEndText()
        self.checkTestHeader()

    def checkEndText(self):
        if self.inText:
            self.inText = False
            self.out << Close << Flush

    def checkTestHeader(self):
        if len(self.loggedStack) and not self.loggedStack[-1]:
            self.loggedStack[-1] = 1
            
            id = "testHead-%s" % "/".join(self.testStack)
            self.out << Header(level=2, id=id) << " > ".join(self.testStack[1:]) << Close
    
    def close(self):
        self.checkEndText()

    def flush(self):
        self.out << Flush
            
    def writeText(self, text):
        self.out.write(text)
        
    def write(self, text):
        if not text:
            return
        
        if self.inBlock or self.inText:
            self.out << escapeHTML(text) << Flush
        else:
            self.checkTestHeader()
            
            # XXXjoe We have to close the block here or the browser won't render the <pre>
            self.out << CodeBlock("log") << escapeHTML(text) << Close << Flush
            # self.inText = True

    # **********************************************************************************************
    # Commands
    
    def beginBlock(self, name=""):
        self.checkLooseEnds()
        self.inBlock += 1

        classes = " ".join(["log-%s" % name for name in name.split(" ")])
        self.out << Block("log %s" % classes) << Flush
    
    def endBlock(self):
        self.inBlock -= 1
        self.checkLooseEnds()

        self.out << Close << Flush

    def beginRawText(self):
        self.out << CodeBlock("log rawText")

    def endRawText(self):
        self.out << Close << Flush

    def beginVariable(self, name="", value=""):
        self.checkLooseEnds()
        self.inBlock += 1

        self.out << Block("variable") \
            << Table("variableTable", cellspacing="0", cellpadding="0") \
                << Row \
                    << Cell("variableName") << name << " = " << Close \
                    << Cell("variableValue") << escapeHTML(value) << Close \
                << Close \
            << Close \
        << Close << Flush

    def endVariable(self):
        self.inBlock -= 1
        self.checkLooseEnds()
    
    # Links
    
    def link(self, href="", text=""):
        if not text:
            text = href
        self.out << Link(href=href) << text << Close
        
    def fileLink(self, fileName="", line=0, column=0, rowType=""):
        fileName = fileName.replace("\\", os.sep)
        name = fileName.split(os.sep)[-1]
    
        self.out \
            << FileLink("problemLink", basePath=self.project.path, path=fileName,
                lineNo=line, rowType=rowType) \
                << ("%s (line %s)" % (name, line)) \
            << Close
            
    # Debugging

    def reach(self, fileName="", line=0):
        self.checkLooseEnds()

        self.beginBlock("reach")
        self.out << "Reachpoint"
        self.fileLink(fileName, line)
        self.endBlock()

    def constructObject(self, id="", typeName=""):
        self.checkLooseEnds()

        self.out << Script << "objectCreated('%s', '%s')" % (id, typeName) << Close
        self.beginBlock("lifetime create")
        self.out << "Construct %s" % typeName
        self.endBlock()
        
    def destroyObject(self, id="", typeName=""):
        self.checkLooseEnds()

        self.out << Script << "objectDestroyed('%s')" % id << Close << Flush
        self.beginBlock("lifetime destroy")
        self.out << "Destroy %s" % typeName
        self.endBlock()

    # Tables
    
    def beginTable(self, name=""):
        self.checkLooseEnds()

        self.out \
            << Block("tableBox") \
                << Table("logTable", cellspacing="0", cellpadding="0") << Flush
    
    def endTable(self):
        self.out << Close << Close << Flush
    
    def beginRow(self, rowType=""):
        self.out << Row("rowType-%s" % rowType) << Flush
    
    def endRow(self):
        self.out << Close << Flush
    
    def cell(self, value=""):
        self.out << Cell << value << Close << Flush
                
    # Trees
    
    def beginTree(self, name=""):
        self.checkLooseEnds()

        self.out \
            << UnorderedList("treeBox") << Flush

    def endTree(self):
        self.out << Close << Flush

    def treeNode(self, value=""):
        self.out << ListItem("treeItem") << value << Close << Flush

    # Test Results

    def beginTest(self, name):
        self.checkEndText()

        self.testStack.append(name)
        self.loggedStack.append(0)

        id = "testBegin-%s" % "/".join(self.testStack)
        self.out << Script << ('beginTest("%s")' % name) << Close \
            << Link(id=id) << Close << Flush
    
    def endTest(self):
        self.checkEndText()
        self.out << Script << 'endTest()' << Close << Flush

        self.testStack.pop()
        self.loggedStack.pop()
    
    def assertionFailed(self, title="Assertion", expected="", actual="", message="",
                            fileName="", line=0, column=0, **kwds):
        self.testErrorCount += 1
        self.contractFailed(title, expected, actual, message, fileName, line, fromTest=True,
            **kwds)

    def testExceptionThrown(self, title="Exception", message="", fileName="", line=0, column=0):
        self.testErrorCount += 1

        self.checkLooseEnds()

        # XXXjoe This is really annoying me, but it might be helpful in some situations...
        
        #self.out \
        #    << Script << 'testExceptionThrown()' << Close \
        #    << Block("log log-warn") << "Exception was not caught! (%s)" % message \
        #    << Close
            
    def exceptionThrown(self, title="Exception", message="", fileName="", line=0, column=0,
        fromTest=False):

        self.checkLooseEnds()

        self.out \
            << Script << 'exceptionThrown()' << Close
        
        self.out \
            << Block("problemBox problem-exception") \
                << Span("problemTitle") << title << Close

        if fileName:
            self.fileLink(fileName, line, rowType="primary")

        if message:
            self.out \
                << Table("problemTable", cellspacing="0", cellpadding="0") \
                    << Row \
                        << Cell("problemRowName") << "Message: " << Close \
                        << Cell("problemRowValue") << escapeHTML(message) << Close \
                    << Close \
                << Close

        self.out << Close << Flush

    def contractFailed(self, title="Assertion", expected="", actual="", message="", fileName="",
                        line=0, column=0, excName="", excMessage="", fromTest=False, **kwds):
        self.checkLooseEnds()

        if fileName:
            fullPath = "" #devon.jump.expandPath(self.project, fileName)
            name = fileName.split(os.sep)[-1]
        else:
            name = ""
        
        actualKey = ""
        expectedKey = ""

        # Search for the keys for the actual and expected rows
        varIndex = 0
        while True:
            keyName = "var%d" % varIndex
            keyVal = "val%d" % varIndex
            if not keyName in kwds or not keyVal in kwds:
                break

            if kwds[keyName] == "Actual":
                actualKey = keyVal
            elif kwds[keyName] == "Expected":
                expectedKey = keyVal
            
            varIndex += 1

        if actualKey and expectedKey: 
            actual = kwds[actualKey]
            expected = kwds[expectedKey]
            pre, diff, post = diffStrings(actual, expected)
            line = int(line) + len(pre.split("\\n"))

        if fromTest:        
            self.out \
                << Script << 'assertionFailed()' << Close
        else:
            self.out \
                << Script << 'contractFailed()' << Close

        self.out \
            << Block("problemBox problem-exception")

        if excName:
            self.out \
                << Span("problemTitle") << excName << Close \
                << Table("problemTable", cellspacing="0", cellpadding="0") \
                    << Row \
                        << Cell("problemRowName") << "Message:" << Close \
                        << Cell("problemRowValue") << escapeHTML(excMessage) << Close \
                    << Close \
                << Close 

        if fileName:
            self.fileLink(fileName, line, rowType="primary")
                
        self.out \
            << Span("problemTitle") << title << Close \
            << Table("problemTable", cellspacing="0", cellpadding="0")

        varIndex = 0
        while True:
            keyName = "var%d" % varIndex
            keyVal = "val%d" % varIndex
            if not keyName in kwds or not keyVal in kwds:
                break

            self.out \
                << Row \
                    << Cell("problemRowName") << kwds[keyName] << ":" << Close \
                    << Cell("problemRowValue")
                        
            if keyVal == actualKey and expectedKey:
                self.out << escapeHTML(pre) \
                    << Strong << "*" << escapeHTML(diff) << "*" << Close \
                    << escapeHTML(post)
                        
            else:
                self.out << escapeHTML(kwds[keyVal])
                
            self.out << Close << Close
            
            varIndex += 1
        
        self.out \
            << Close \
            << Close << Flush

    def arrayAssertionFailed(self, result, expected="", actual="", message="", fileName="", line=0, column=0):
        fullPath = "" #devon.jump.expandPath(self.project, fileName)
        name = fileName.split(os.sep)[-1]

        self.out \
            << Block("problemBox") \
                << FileLink("resultLink", path=fullPath, lineNo=line, rowType="primary") \
                    << name \
                << Close \
                << ": %s - %s" % (actual, expected) \
            << Close << Flush

    def programExit(self):
        self.exitSucceeded = True
        
def escapeJS(text):
    return text.replace("\n", "\\n").replace('"', '\\"')

def escapeHTML(text):
    return text.replace("\\n", "\n")

def pathToTestId(path):
    return path.replace("/", "*")

def testIdToPath(path):
    return path.replace("*", "/")

def getProjectTargetName(project):
    targetPath = project.getBuildTarget()
    if targetPath:
        return os.path.basename(targetPath)
    else:
        return os.path.basename(project.path)

def getProjectTestModule(project):
    return getProjectTargetName(project) + ".test"

def diffStrings(actual, expected):
    lenActual = len(actual)

    i = 0
    for i in xrange(0, len(expected)):
        if i >= lenActual or not (actual[i] == expected[i]):
            postExpected = expected[i:]
            for e in xrange(i+1, len(expected)):
                found = postExpected.find(actual[e:])
                if not found == -1:
                    return actual[0:i], actual[i:e], actual[e:]
            
            break

    return actual[0:i], actual[i:], ""

def runCommand(commandPath, args, handler, project, debugger, out):
    pyEnv = initPythonEnvironment(project)

    print ">>> %s %s" % (commandPath, " ".join(args))

    reader = devon.log.LogReader(commandPath, args, debugger=debugger)
    if not reader.pid:
        return

    out << Script << ("parent.runBegin(%d);" % reader.pid) << Close

    reader.process(handler)

    out << Script << ("parent.runEnd(%d);" % reader.pid) << Close

    restorePythonEnvironment(pyEnv)
