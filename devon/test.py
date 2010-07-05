
import devon.log
import inspect, types, sys, traceback, os.path, re, cgi, imp, glob, functools, unittest, shutil
from importing import *
   
# **************************************************************************************************
     
UnknownType = 0
FixtureType = 1
SuiteType = 2
WrapperType = 3
FunctionType = 4
InspectorType = 5
ExeType = 6

testTypeNames = {
    UnknownType: "Unknown",
    FixtureType: "Fixture",
    SuiteType: "Suite",
    WrapperType: "Wrapper",
    FunctionType: "Function",
    InspectorType: "Inspector",
    ExeType: "Exe",
}

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

reFixturePrefix = re.compile("(.*?)Tests")
reFunctionPrefix = re.compile("test(.+)")

reTestSep1 = re.compile("^={3,}$")
reTestSep2 = re.compile("^(- ){3,}[-]?$")
reFocus = re.compile("^\\\{3,}?$")
reDisabler = re.compile("^///{3,}?$")
reComment = re.compile("#\s*(.*)\s*$")
reArg = re.compile("%\s*(.*)\s*$")
reArgPair = re.compile("%\s*(.+?)\s*:\s*(.+?)\s*$")

# **************************************************************************************************
    
def testFunctionPrefix(name):
    m = reFunctionPrefix.match(name)
    if m:
        testPrefix = m.groups()[0]
        return testPrefix[0].lower() + testPrefix[1:]

def functionNameToTestFilePattern(obj, name):
    # Find the directory of the module that the class belongs to    
    modFilePath = findModule(obj.__module__)
    modFileDirPath = os.path.dirname(modFilePath)
    
    return os.path.join(modFileDirPath, "%s*.test" % name)
    
def testFileName(obj, name):
    # Find the directory of the module that the class belongs to    
    modFilePath = findModule(obj.__module__)
    modFileDirPath = os.path.dirname(modFilePath)
    
    return os.path.join(modFileDirPath, "%s.test" % name)

def testFileFunctionName(filePath):
    fileName = os.path.basename(filePath)
    fnPrefix,ext = os.path.splitext(fileName)
    fnPrefix = fnPrefix[0].upper() + fnPrefix[1:]
    return "test%s" % fnPrefix

def testFileFunctionHiddenName(name):
    return "__%s__" % name

# **************************************************************************************************

class TestCase:
    class __metaclass__(type):
        def __new__(cls, *args):
            newClass = super(cls, cls).__new__(cls, *args)

            for name in dir(newClass):
                attr = getattr(newClass, name)
                if type(attr) == types.UnboundMethodType:
                    args, varags, varkwds, defaults = inspect.getargspec(attr)
                    if len(args) < 2:
                        continue

                    functionName = testFunctionPrefix(name)
                    if not functionName:
                        continue
                    
                    delattr(newClass, name)
                    hiddenName = testFileFunctionHiddenName(functionName)
                    setattr(newClass, hiddenName, attr)
                    
                    # Create a new function for every test file whose name matches the class name
                    pattern = functionNameToTestFilePattern(newClass, functionName)
                    for filePath in glob.glob(pattern):
                        fnName = testFileFunctionName(filePath)
                        setattr(newClass, fnName, TestFileFunc(newClass, filePath, hiddenName))
                
            return newClass
    
    def __new__(cls, *args):
        obj = object.__new__(cls, *args)
        for name in dir(obj):
            value = getattr(obj, name)
            if isinstance(value, TestFileFunc): 
                setattr(obj, name, TestFileFunc(fixture=obj, filePath=value.testFilePath,
                    methodName=value.methodName))
        return obj

    def __init__(self, testName=None, writer=None):
        self.testName = testName
        self.writer = writer
        
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def assert_(self, truth):
        if not truth:
            raise TestException("Assertion")

    def assertEqual(self, actual, expected):
        if not actual == expected:
            raise TestException("Equality Assertion", Actual=str(actual), Expected=str(expected))

    def assertEqualString(self, actual, expected):
        a = str(actual).strip()
        e = str(expected).strip()
        if not a == e:
            raise TestException("Equality Assertion", Actual=a, Expected=e)
   
    def assertNotEqual(self, actual, expected):
        if actual == expected:
            raise TestException("Not Equal Assertion", Actual=str(actual), Expected=str(expected))

    def assertIn(self, item, container):
        if not item in container:
            raise TestException("Contained Assertion", item=str(item), container=str(container))
   
    def assertNotIn(self, item, container):
        if item in container:
            raise TestException("Not Contained Assertion",
                item=str(item), container=str(container))

    def assertType(self, actual, expected):
        if not isinstance(actual, expected):
            raise TestException("Type Assertion", Actual=str(actual), Expected=str(expected))
    
    def assertException(self, expected):
        actual = "Exception: %s" % sys.exc_value
        if not actual == expected:
            logException(log)
            raise TestException("Exception Assertion", Actual=str(actual), Expected=str(expected))
    
    def log(self, obj):
      from pprint import pprint
      pprint(obj)

    def logAttributes(self, object, *names):
      lines = []
      for name in names:
        value = getattr(object, name)
        line = "%s: %s" % (name, value)
        lines.append(line)
        
      result = "\n".join(lines)
      print result, "\n"
      
    def warn(self, message):
        print message
    
    def fail(self):
        raise TestException("Failure")
    
# **************************************************************************************************

class TestException(Exception):
    def __init__(self, title, **vars):
        self.title = title
        self.vars = vars

# **************************************************************************************************

class TestRunner:
    def __init__(self, fixtureName, writer=None, order=None):
        self.fixtureName = fixtureName        
        self.fixtureClass = importObject(fixtureName)
        self.order = order
        assert self.fixtureClass, "Fixture not found"

        self.writer = writer or devon.log.LogWriter()
        
    def getTestNames(self):
        for attrName in dir(self.fixtureClass):
            if attrName.find("test") != 0 and attrName.find("inspect") != 0:
                continue
                
            attrValue = getattr(self.fixtureClass, attrName)
            if callable(attrValue):
                if hasattr(attrValue, "__status__"):
                    testStatus = attrValue.__status__
                    if testStatus == "ignore":
                        continue
                else:
                    testStatus = ""

                if isinstance(attrValue, TestFileFunc) and attrValue.fixture != self.fixtureClass:
                    continue
                yield attrName, FunctionType, testStatus

    def runTest(self, targetName=None, fixtureName=None):
        for testName, testType, testStatus in self.getTestNames():
            if not testStatus == "skip" and (not targetName or testName == targetName):
                self.fixture = self.fixtureClass(testName, self.writer)

                self.writer.cmd.beginTest(name=self.fixtureName)
                success = self.run(testName)
                self.writer.cmd.endTest()

    def setUp(self):
        try:
            self.fixture.setUp()
            return True

        except Exception,exc:
            logException(self.writer)
            return False

    def tearDown(self):
        try:
            self.fixture.tearDown()
            return False

        except Exception,exc:
            logException(self.writer)
            return False
    
    def run(self, name):
        test = getattr(self.fixture, name)
        if hasattr(test, "testContainer"):
            failures = 0
            
            self.writer.cmd.beginTest(name="%s" % name)

            for childTest, fileName, lineNo in test():
                self.writer.cmd.beginTest(name="%s:%s" % (name, lineNo))
                self.setUp()            

                success = self.callTest(childTest, fileName, lineNo)
                if not success:
                    failures += 1

                self.tearDown()
                self.writer.cmd.endTest()

            self.writer.cmd.endTest()
            
            return not failures
        else:
            self.writer.cmd.beginTest(name=name)
            self.setUp()            

            success = self.callTest(test)

            self.tearDown()
            self.writer.cmd.endTest()
            return success
            

    def callTest(self, test, fileName=None, lineNo=None):
        try:
            test()
            return True
        except TestException, exc:
            if not fileName:
                fileName, lineNo = getTracebackSource()

            logAssertion(self.writer, exc, fileName, lineNo)
            return False

        #except AssertionError, exc:
        #    if not fileName:
        #        fileName, lineNo = getTracebackSource()
        #
        #    logUnitTestAssertion(self.writer, exc, fileName, lineNo)
        #    return False

        except:
            logException(self.writer)
            return False

# **************************************************************************************************

class TestFileFunc:
    def __init__(self, fixture, filePath, methodName):
        self.fixture = fixture
        self.testFilePath = filePath
        self.methodName = methodName
        self.testContainer = True
        
    def __call__(self):
        fn = getattr(self.fixture, self.methodName)
        
        testFilePath = testFilesPath(self.testFilePath)
        
        for source,expected,args,files,lineNo in walkTextTests(self.testFilePath):
            for testPath in files:
                subPath = os.path.dirname(testPath)
                dirPath = os.path.join(testFilePath, subPath)
                fileName = os.path.basename(testPath)
                filePath = os.path.join(dirPath, fileName)
                if not os.path.isdir(dirPath):
                    os.makedirs(dirPath)
                
                f = file(filePath, "w")
                f.write(files[testPath])
                f.close()
            
            printFn, copyOutput, testFn = self.extractArgs(args, "print", "copy", "test")
            printOutput = printFn and not callable(printFn)
            
            if testFn:
                runner = functools.partial(self.runTest, testFn, source, expected, args,
                    copyOutput, printOutput, printFn)
            else:
                runner = functools.partial(self.runTest, fn, source, expected, args,
                    copyOutput, printOutput, printFn)

            sys.path.append(os.path.dirname(self.testFilePath))
            sys.path.append(testFilePath)

            yield runner, self.testFilePath, lineNo

            sys.path.remove(os.path.dirname(self.testFilePath))
            sys.path.remove(testFilePath)
            
            if os.path.isdir(testFilePath):
                shutil.rmtree(testFilePath)

    def extractArgs(self, args, *names):
        for name in names:
            if not name in args:
                yield None
            else:
                value = args[name]
                del args[name]

                if not isinstance(value, str):
                    yield True
                else:
                    hiddenName = testFileFunctionHiddenName(value)
                    if hasattr(self.fixture, hiddenName):
                        fn = getattr(self.fixture, hiddenName)
                        yield fn
                    else:
                        self.fixture.warn("Test '%s' is not defined" % value)
                        yield None

    def runTest(self, fn, source, expected, args, copyOutput, printOutput, printFn):
        try:
            if callable(printFn):
                print printFn(source, expected, **args)

            actual = fn(source, expected, **args)
            if copyOutput:
                copyToClipboard(actual)
            if printOutput:
                print actual
            if actual != None:
                self.fixture.assertEqualString(actual, expected)
        #except AssertionError, exc:
        #    raise
        except TestException, exc:
            raise
        except:
            self.fixture.assertException(expected)

testFilesDirName = "__tests__"

def testFilesPath(path):
    return os.path.join(os.path.dirname(path), testFilesDirName)
    
# **************************************************************************************************
# Decorators

def skip():
    """ Decorator for marking test function that should not be executed."""
    
    def wrapper(fn):
        fn.__status__ = "skip"
        return fn
    
    return wrapper

# **************************************************************************************************

def runTests(targetPath):
    """ Runs all tests within the target."""
    
    installLogging()

    writer = devon.log.LogWriter()
    writer.cmd.beginTest(name="Tests")

    targetPaths = targetPath.split("/")
    
    try:
        if len(targetPaths) == 3:
            testName = targetPaths[2] if len(targetPaths) > 2 else None
            testRunner = TestRunner(targetPaths[1], writer)
            testRunner.runTest(testName)
        elif len(targetPaths) == 2:
            moduleName,fixtureName = targetPaths[1].rsplit(".", 1)
            for testRunner in walkModuleTestRunners(moduleName, writer, fixtureName):
                testRunner.runTest()
        elif len(targetPaths) == 1:
            for testRunner in walkModuleTestRunners(targetPath, writer):
                testRunner.runTest()
    except:
        logException(writer)
            
    writer.cmd.endTest()
    writer.cmd.programExit()

def runExe(targetName, *args):
    """ Runs an executable identified by an object's module path."""
    
    installLogging()

    moduleNames = targetName.split(".")
    moduleName = ".".join(moduleNames[0:-1])
    fnName = moduleNames[-1]

    try:
        fn = __import__(moduleName)
        for name in moduleNames[1:]:
            fn = getattr(fn, name)

        fn(*args)
    except:
        name,line = getTracebackSource()
        msg = traceback.format_exc()
        log.cmd.exceptionThrown(message=escape(msg), fileName=name, line=line)
    
    log.cmd.programExit()

def writeTestCatalog(moduleName):
    """Reads the list of testable modules from the input file and writes out the list of tests
        they contain to the output file."""
     
    outputFilePath = devon.log.getLogPath("DevonTestCatalogOutput.txt")
    writer = devon.log.LogWriter(log=outputFilePath)

    writer.cmd.declareTest(name="Tests", testType=SuiteType)
    
    for testRunner in walkModuleTestRunners(moduleName, writer, printStack=True):
        testNames = [(testName, testType, testStatus) \
            for testName, testType, testStatus in testRunner.getTestNames()]
        if len(testNames) == 0:
            continue

        end = testRunner.fixtureName.rfind(".test.")
        suiteName = testRunner.fixtureName[end+6:]
        writer.cmd.declareTest(name=suiteName, testType=FixtureType, id=testRunner.fixtureName)
        
        for testName, testType, testStatus in testNames:
            writer.cmd.declareTest(name=testName, testType=testType, testStatus=testStatus)
            writer.cmd.endDeclareTest()
        
        writer.cmd.endDeclareTest()
    writer.cmd.endDeclareTest()
        
# **************************************************************************************************

def installLogging():
    import devon.log
    log = devon.log.LogWriter()

    import __builtin__
    __builtin__.log = log

    import sys
    sys.stdout1 = sys.stdout
    sys.stdout = log

def getTracebackSource(exc=None):
    if not exc:
        exc = sys.exc_info()
        
    try:
        msg, (filename, lineno, offset, badline) = exc[1]
        return filename, lineno
    except:
        tb = exc[2]
        while tb.tb_next:
            tb = tb.tb_next
        
        try:
            info = inspect.getframeinfo(tb.tb_frame)
            return info[0:2]
        except:
            return (None,None)

def escape(text):
    text = cgi.escape(text, True)
    text = text.replace('\n', '&#010;')
    text = text.replace('\r', '&#010;')
    return text

def copyToClipboard(text):
    assert sys.platform == "darwin", "Clipboard copying only supported on Mac OS X"

    stream = os.popen("pbcopy", "w")
    stream.write(text)
    stream.close()
        
# **************************************************************************************************

def logAssertion(writer, exc, fileName, lineNo):
    varIndex = 0
    vars = {}
    for name in exc.vars:
        vars["var%d"%varIndex] = name
        vars["val%d"%varIndex] = escape(exc.vars[name])
        varIndex += 1

    writer.cmd.assertionFailed(title=escape(exc.title), fileName=escape(fileName), line=lineNo,
        **vars)

def logUnitTestAssertion(writer, exc, fileName, lineNo):
    vars = {"var0": "Message", "val0": escape(str(exc))}

    writer.cmd.assertionFailed(title="Assertion",
        fileName=escape(fileName), line=lineNo, **vars)

def logException(writer, printStack=False):
    fileName, lineNo = getTracebackSource()
    description = traceback.format_exc()

    if printStack:
        print description
    
    writer.cmd.exceptionThrown(message=escape(description),
        fileName=escape(fileName), line=lineNo)
    writer.cmd.testExceptionThrown(message=escape(description),
        fileName=escape(fileName), line=lineNo)

# **************************************************************************************************

def walkModuleTestRunners(moduleName, writer, fixtureName=None, printStack=False):
    """ Yields a TestRunner for every test case found within a branch of modules."""
    
    def sortOrder(a, b):
        return 1 if a.order > b.order else (-1 if a.order < b.order else 0)
    
    for moduleName in walkModuleNames(moduleName):
        try:
            runners = list(walkSingleModuleTestRunners(moduleName, writer, fixtureName))
            runners.sort(sortOrder)
            for runner in runners:
                yield runner
        except:
            logException(writer, printStack)

def walkSingleModuleTestRunners(moduleName, writer, fixtureName=None):
    """ Yields a TestRunner for each test case found within a single module. """
    
    try:
        module = importModule(moduleName)
    except ImportError, exc:
        print traceback.format_exc()
        return
    
    for attrName in dir(module):
        attrValue = getattr(module, attrName)
        
        if (issubclass(type(attrValue), types.TypeType) \
            or issubclass(type(attrValue), types.ClassType)) \
            and (issubclass(attrValue, TestCase) or issubclass(attrValue, unittest.TestCase)) \
            and attrValue.__module__ == moduleName:
            
            if not fixtureName or attrName == fixtureName:
                testName = ".".join((moduleName, attrName))
                order = getattr(attrValue, "order", None)
                runner = TestRunner(testName, writer, order=order)
                yield runner

def walkTextTests(testFilePath):
    lines = [line for line in file(testFilePath)]
    if reTestSep1.match(lines[0]) or reFocus.match(lines[0]):
        return walkTextBlocks(lines, testFilePath)
    else:
        return walkTextRows(lines, testFilePath)
    
def walkTextBlocks(lines, testFilePath):
    global expected, allArgs, testArgs, testFiles

    blocks = []
    focusedBlocks = []
    
    # Block properties
    tests = []
    source = []
    expected = []
    globalArgs = {}
    allArgs = {}
    testArgs = {}
    testFiles = {}
    expectedLine = 0
    lineNo = 0
     
    # State flags
    consuming1a = False
    consuming1b = False
    consuming2a = False
    consuming2b = False
    bail = False
    focused = False
    nextFocused = False

    def addTest():
        global expected, allArgs, testArgs, testFiles
        
        args = dict(globalArgs)
        args.update(allArgs)
        args.update(testArgs)
        coerceArgs(args)
        
        if "skip" not in testArgs:
            expected = "".join(expected).strip()
            if "file" in args:
                testFiles[args["file"]] = expected
            else:
                test = (source, expected, args, testFiles, expectedLine)
                tests.append(test)
        
        expected = []
        testArgs = {}
        return tests
        
    def consumeArg(args, line):
        m = reComment.match(line)
        if m:
            return True
        
        m = reArgPair.match(line)
        if m:
            args[m.groups()[0]] = m.groups()[1]
            return True
            
        else:
            m = reArg.match(line)
            if m:
                instruction = m.groups()[0]
                args[instruction] = True
                
                return True
                
    for line in lines:
        lineNo += 1
        
        if consuming1a:
            if reFocus.match(line):
                focused = True    
                
            elif not consumeArg(allArgs, line):
                consuming1a = False
                consuming1b = True
            
        if consuming1b:
            bail = reDisabler.match(line)
            
            if reTestSep2.match(line):
                consuming1b = False
                consuming2a = True
                expectedLine = lineNo
                source = "".join(source).strip()

            elif bail or reTestSep1.match(line):
                globalArgs.update(allArgs)

                consuming1b = False
                consuming1a = True    

                if bail:
                    break
            else:
                source.append(line)

        elif consuming2a:
            if not consumeArg(testArgs, line):
                consuming2a = False
                consuming2b = True
                expected.append(line)

        elif consuming2b:
            bail = reDisabler.match(line)
            if reTestSep2.match(line):
                addTest()
                consuming2a = True
                
            elif bail or reTestSep1.match(line):
                if focused:
                    focusedBlocks += addTest()
                else:
                    blocks += addTest()

                if bail:
                    break
                
                tests = []
                source = []
                allArgs = {}
                testFiles = {}
                focused = nextFocused
                nextFocused = False
                consuming2b = False
                consuming1a = True
            else:
                expected.append(line)

        elif reFocus.match(line):
            focused = True    

        elif reTestSep1.match(line):
            consuming1a = True    
    
    return blocks if not focusedBlocks else focusedBlocks
    
def walkTextRows(lines, testFilePath):
    source = []
    expected = []
    expectedLine = 0
    lineNo = 0
    
    for line in lines:
        lineNo += 1
                            
        if line == "\n":
            if expected:
                expected = "\n".join(expected)
                for item in source:
                    yield item, expected, {}, {}, expectedLine
            
            source = []
            expected = []
        
        elif line[0] == "#":
            pass
        elif line[0] == " ":
            expected.append(line.strip())
            expectedLine = lineNo
        else:
            source.append(line.strip())

    if expected:
        expected = "\n".join(expected)
        for item in source:
            yield item, expected, {}, {}, expectedLine

def coerceArgs(args):
    for name,value in args.iteritems():
        try:
            args[name] = int(value)
        except:
            if value.lower() == "false":
                args[name] = False
            elif value.lower() == "true":
                args[name] = True

