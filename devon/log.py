import os.path, time, sys, threading, thread, xml.dom.pulldom

# **************************************************************************************************

messageBegin = "%c" % 1
messageEnd = "%c" % 2

global logPath
if sys.platform == "win32":
    logPath = "c:/temp"
else:
    logPath = "~"

global logFilePath
logFilePath = os.path.join(os.path.expanduser(logPath), "DevonLog.txt")

# **************************************************************************************************

class LogWriter:
    def __init__(self, log=None):
        if not log:
            global logFilePath
            log = logFilePath

        self.logFile = file(log, "a")
        self.fileno = self.logFile.fileno
        self.cmd = Commander(self)
        
    def __lshift__(self, text):
        if isinstance(text, str):
            self.write(text)
        else:
            self.write(str(text))
        return self
        
    def write(self, text):
        self.logFile.seek(0, 2)
        self.logFile.write(text)
        self.logFile.flush()

    def log(self, text):
        self.logFile.seek(0, 2)
        self.logFile.write(text)
        self.logFile.flush()

    def logMessage(self, text):
        self.logFile.seek(0, 2)
        self.logFile.write(messageBegin)
        self.logFile.write(text)
        self.logFile.write(messageEnd)
        self.logFile.flush()

    def logCommand(self, commandName, *args, **keyArgs):
        self.logFile.seek(0, 2)
        self.logFile.write(messageBegin)
        self.logFile.write("<%s" % commandName)
        for key in keyArgs:
            value = escapeXML(keyArgs[key])
            self.logFile.write(' %s="%s"' % (key, value))
        self.logFile.write("/>\n")
        self.logFile.write(messageEnd)
        self.logFile.flush()

    def flush(self):
        self.logFile.flush()

# **************************************************************************************************

class LogReader:
    def __init__(self, command, args, log=None, debugger=False):
        if not log:
            global logFilePath
            self.logPath = logFilePath
        else:
            self.logPath = log

        # Erase the file first so we don't read the previous output
        f = file(self.logPath, "w")
        f.close()
        
        dirPath = os.path.dirname(command)
        if dirPath:
            os.chdir(dirPath)
        if debugger:
            gdbCommand = "/usr/bin/gdb"
            debugArgs = ["--args", command] + args
            command = "gdb --args %s %s" % (command, " ".join(args))

            self.pid = os.spawnlp(os.P_NOWAIT, gdbCommand, gdbCommand, *debugArgs)
        else:
            # Spawn a process which we expect to write output to DevonLog.txt
            self.pid = os.spawnlp(os.P_NOWAIT, command, command, *args)
        
        if self.pid:
            self.deadEvent = threading.Event()
            thread.start_new_thread(waitOnProcess, (self.pid, self.deadEvent))

    def process(self, handler):
        self.buffer = ""
        
        for text in self.readLines():
            self.__processText(text, handler)
            handler.flush()
            
        handler.close()
        
    def readLines(self):
        # Open the file to poll for new text
        f = file(self.logPath, "r")
    
        # While the process is running, poll the file for new text
        while not self.deadEvent.isSet():
            t = self.__pollFile(f)
            if t:
                yield t
    
            time.sleep(0.2)
    
        t = self.__pollFile(f)
        if t:
            yield t
            
        f.close()

    def __processText(self, text, handler):
        """ Parses the process output as an xml stream. If the handler has a function corresponding
            to an output node, it will be called with the appropriate arguments. """
        
        self.buffer += text    
    
        startIndex = self.buffer.find(messageBegin)            
        while startIndex >= 0:
            preText = self.buffer[0:startIndex]
            if preText:
                handler.write(preText)
            
            endIndex = self.buffer.find(messageEnd, startIndex)
            if endIndex == -1: 
                self.buffer = self.buffer[startIndex:]
                return
                           
            else:
                messageText = self.buffer[startIndex+1:endIndex]
                self.buffer = self.buffer[endIndex+1:]
    
                try:
                    message = xml.dom.pulldom.parseString(messageText)
                    node = message.getEvent()[1].documentElement
    
                    if hasattr(handler, node.nodeName):
                        args = {}
                        for i in xrange(0, node.attributes.length):
                            attr = node.attributes.item(i)
                            args[str(attr.nodeName)] = str(attr.nodeValue)
                        
                        fn = getattr(handler, node.nodeName)
                        try:
                            fn(**args)
                        except:
                            import sys, traceback
                            exc = sys.exc_info()
                            traceback.print_exception(*exc)

                except:
                    # Bad XML - just ignore it and move on
                    print "Invalid markup: '%s'" % messageText
                
            startIndex = self.buffer.find(messageBegin)
    
        if self.buffer:
            handler.write(self.buffer)
            self.buffer = ""

    def __pollFile(self, f):
        text = ""
        t = f.readline()
        while t:
            text += t
            t = f.readline()
    
        return text

# **************************************************************************************************

class Commander:
    def __init__(self, log):
        self.__dict__["log"] = log
        
    def __getattr__(self, name):
        def write(*args, **kwds):
            return self.__dict__["log"].logCommand(name, *args, **kwds)
        return write
        
# **************************************************************************************************

def waitOnProcess(pid, deadEvent):
    os.waitpid(pid, 0)
    deadEvent.set()

def escapeXML(text):
    if not isinstance(text, basestring):
        text = str(text)

    return text.replace('"', '\\"')

def getLogPath(logName):
    global logPath
    return os.path.join(os.path.expanduser(logPath), logName)
        
        