
import sys, os.path
import codeop, cgi, datetime, imp, mimetypes, re, signal, thread, threading
import traceback, types, urllib, time
import BaseHTTPServer, SocketServer 
import devon.stream, devon.renderers.html, devon.projects

# **************************************************************************************************
# Globals

global sites, messageEvent, resumeEvent, userEvent, currentProcess, userEventObject, done, server

sites = {}
fileCache = {}
pageCache = {}
messageEvent = None
resumeEvent = None
currentProcess = None
done = False
server = None

# **************************************************************************************************
# Constants

webPort = 3800

kConfigFileName = "config.py"

# **************************************************************************************************

class WebServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Multi-threaded version of the basic web server"""
    pass
    
class WebRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Handler that is called on a new thread to handle an HTTP request"""
    
    __reCommand = re.compile("/([^\s:]+):(.*?)$")
    __reArgs = re.compile("(?P<name>[^#=&]+)=(?P<value>[^&]*)&?")

    # Override logging
    def log_message(self, format, *args):

        pass
        
    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def do_POST(self):
        self.data = self.rfile.read(int(self.headers["content-length"]))
        self.do_GET()
        
    def do_GET(self):
        global sites
        
        if self.client_address[0] != "127.0.0.1":
            pass #return self.serveError(401, "Unauthorized")

        self.__parseHost()
        self.__parseURL()

        if not self.host or not self.host in sites:
            self.projects = sites[sites.keys()[0]]
            pass #return self.serveError(404, "Project not found")
        else:
            self.projects = sites[self.host]

        self.project = self.projects[-1]
        
        renderer = devon.renderers.html.HTMLRenderer()
        self.out = devon.stream.OutStream(self.wfile, renderer)

        if not self.command and not self.path:
            self.command = "index"
            self.path = ""
        
        if self.command == "file":
            self.serveProjectFile(self.path)
        elif self.command:
            self.serveCommand(self.command)
        else:
            self.serveFile(self.path)

    def __lshift__(self, text):
        self.out.write(text)
        return self.out
        
    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def getTargetProject(self):
        if self.path:
            return devon.projects.load(self.path)

        if len(self.projects):
            return self.projects[0]
    
    def serveCommand(self, command):
        commandPath = os.path.join(devon.webPath, "%s.py" % command)
        
        if os.path.isfile(commandPath):
            try:
                moduleName = "devon_command_%s" % re.sub("[\./\\\]", "_", commandPath)
                module = imp.load_source(moduleName, commandPath, file(commandPath))

                if hasattr(module, "main"):
                    module.main(self)
                    
            except PipeBrokenError, exc:
                print "Connection was broken"
                
            except ProcessBlockingError, exc:
                self.wfile.write("<div>Another process is already running.</div>")
                self.wfile.write("<script>parent.runBegin(%d);</script>" % exc.pid)
                
            except:
                print "Error during %s..." % self.path
                exc = sys.exc_info()
                traceback.print_exception(*exc)

                self.wfile.write("""<pre class="traceback">""")
                traceback.print_exception(exc[0], exc[1], exc[2], file=self.wfile)
                self.wfile.write("""</>""")

        else:
            self.serveError(404, "Command '%s' not found" % command)

    def serveProjectFile(self, path):
        if not self.project.wikiPath:
            return self.serveError(404, "This project has no wiki")
            
        wikiPath = os.path.join(self.project.path, self.project.wikiPath)
        # print "wikiPath %s" % wikiPath
        
        wikiProject = devon.projects.load(wikiPath)
        filePath = os.path.join(wikiProject.path, path)
        
        return self.serveRawFile(filePath)
        
    def serveFile(self, path, varNames=None):
        if path == "/":
            return self.serveError(404, "Please specify a project path")
            
        if path[0] == "/":
            path = path[1:]
        
        fullPath = os.path.join(devon.webPath, path)
        if os.path.exists(fullPath):
            self.serveRawFile(fullPath)
    
        else:
            fullPath = self.project.getDocumentPath(self.path)
            if os.path.isfile(fullPath):
                self.serveCommand("wiki")
            else:
                self.serveError(404, "File '%s' not found" % self.path)

    def serveRawFile(self, path):
        mimeType, encoding = mimetypes.guess_type(path)
        if not mimeType:
            mimeType = "text/plain"
    
        self.send_response(200)
        self.send_header("Content-Type", mimeType)
        self.end_headers()
    
        f = file(path, "rb")
        stuff = f.read()
        while stuff:
            self.wfile.write(stuff)
            stuff = f.read()
        f.close()
            
    def servePage(self, pagePath, globalVars=None, localVars=None):
        if not localVars:
            localVars = {}
        
        if not "project" in localVars:
            localVars["project"] = self.project
            
        fullPagePath = os.path.join(devon.webPath, pagePath)
        if os.path.isfile(fullPagePath):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            if fullPagePath in pageCache:
                page = pageCache[fullPagePath]
                
                if page.needsUpdate():
                    page.update()
            else:
                page = WebPage(fullPagePath)
                pageCache[fullPagePath] = page
                page.update()

            page.render(self, globalVars, localVars)
        else:
            self.serveError(404, "File '%s' not found" % pagePath)

    def serveError(self, code, message):
        self.send_response(code)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(message)
    
    def serveText(self, text):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(text)

    def __parseHost(self):
        host = self.headers.getheader("Host")
        if ":" in host:
            host, port = host.split(":")
            
        self.host = host
    
    def __parseURL(self):
        source = urllib.unquote(self.path)
        
        self.command = ""
        self.path = ""
        self.args = {}

        m = self.__reCommand.match(source)
        if m:
            self.command = m.groups()[0]
            source = m.groups()[1]
        else:
            source = source[1:]
            
        index = source.find("?")
        if index == -1:
            if source == "/":
                self.path = ""
            else:
                self.path = source
            return
        else:
            self.path = source[0:index]
            source = source[index:]
                
        if source and source[0] == "?":
            m = self.__reArgs.match(source, 1)
            while m:
                gd = m.groupdict()
                self.args[gd["name"]] = gd["value"]
                
                lastOffset = m.end()
                m = self.__reArgs.match(source, m.end())
                if not m:
                    source = source[lastOffset:]

# **************************************************************************************************

class WebPage:
    __reBeginCode = re.compile("<\%")
    __reEndCode = re.compile("\%>")

    def __init__(self, path):
        self.path = path
        self.lastUpdate = None
        self.blocks = None
        
    def needsUpdate(self):
        fileTime = datetime.datetime.fromtimestamp(os.stat(self.path).st_mtime)
        return fileTime > self.lastUpdate
    
    def update(self):
        self.blocks = []
        
        if not os.path.isfile(self.path):
            return
            
        self.lastUpdate = datetime.datetime.now()

        f = file(self.path)
        text = f.read()
        f.close()
        
        index = 0
        m = self.__reBeginCode.search(text)
        while m:
            m2 = self.__reEndCode.search(text, m.end())
            if not m2:
                raise "Syntax Error: Unclosed code block"
            
            textBlock = text[index:m.start()]
            self.blocks.append(textBlock)
            
            codeBlock = text[m.end():m2.start()].strip()
            code = codeop.compile_command(codeBlock, self.path)
            self.blocks.append(code)
            
            index = m2.end()
            m = self.__reBeginCode.search(text, index)

        block = text[index:]
        self.blocks.append(block)
        
    def render(self, request, globalVars=None, localVars=None):
        for block in self.blocks:
            if isinstance(block, types.CodeType):
                exec(block, globalVars, localVars)
            else:
                request.wfile.write(block)

class WebProcess:
    def run():
        pass

# **************************************************************************************************

def serve():
    global sites, done, messageEvent, server

    signal.signal(signal.SIGINT, terminate)
   
    sites = loadSites()
    
    devon.projects.loadExternalProjects()
 
    messageEvent = threading.Event()
      
    # Run the server on a separate thread
    thread.start_new_thread(runServer, ())

    # In a third thread, wait for requests to spawn a process and direct its output through a server
    # request socket. We can't do this in the main thread because we need it to catch signals. (The
    # signal module only delivers signals to the main thread, and not during some blocking system
    # calls like event waits, which we use in this third thread.)
    thread.start_new_thread(awaitMessages, ())
    
    while not done:
        try:
            time.sleep(0.3)
        except IOError:
            # On Windows, Python allows sleep to be interrupted but throws an exc; ignore it
            pass
   
    messageEvent.set()
    server.server_close()
    
    # XXXblake Wait on other threads to shutdown cleanly...

    print "Saving projects..."
    devon.projects.shutdownProjects()
    
def terminate(sig_num, frame):
    # XXXblake
    stopServer()

def runServer():
    print "Starting server..."

    global server
    server = WebServer(("", webPort), WebRequestHandler)
    server.allow_reuse_address = True
    server.serve_forever()

    print "Serve stopped"

def stopServer():
    global done
    done = True    
    messageEvent.set()

def awaitMessages():
    global messageEvent, resumeEvent, userEvent, currentProcess

    resumeEvent = threading.Event()
    userEvent = threading.Event()

    while 1:
        messageEvent.wait()
        if done:
            break
            
        if currentProcess:
            try:
                currentProcess.run()
            except PipeBrokenError, exc:
                print "Connection was broken"
                
            messageEvent.clear()
            resumeEvent.set()
            
def runProcess(process):
    global messageEvent, resumeEvent, currentProcess

    if currentProcess:
        raise ProcessBlockingError(currentProcess.pid)

    # Unblock the main thread so it can run the process
    currentProcess = process 
    messageEvent.set()

    # Wait for the spawned process to complete before exiting
    resumeEvent.wait()
    resumeEvent.clear()
    currentProcess = None

def loadConfigFile(filename):
    path = os.path.join(os.path.expanduser(devon.appPath), filename)
    if not os.path.isfile(path):
        return None
    
    name = filename[:filename.rfind(".")]
    return imp.load_source(name, path, file(path))

def loadSites():
    config = loadConfigFile(kConfigFileName)
    
    sites = {}
    if "sites" in dir(config):
        for siteName in config.sites:
            projectPaths = config.sites[siteName]
            if not (isinstance(projectPaths, tuple) or isinstance(projectPaths, list)):
                projectPaths = [projectPaths]
            
            projects = []
            for projectPath in projectPaths:
                project = devon.projects.load(projectPath)
                if project:
                    projects.append(project)
                    
                    # Load the project's child projects here, too. We would do this anyways when the
                    # project catalog is written, but if we do it here we handle the case where a
                    # site is already loaded (e.g. from a previous session) before Devon is started.
                    
                    project.getChildProjects(True)
                
            sites[siteName] = projects

    return sites

def postUserEvent(event):
    global userEventObject
    userEventObject = event
    userEvent.set()
    
def waitForUserEvent():
    userEvent.wait()
    userEvent.clear()

    global userEventObject
    return userEventObject

# **************************************************************************************************
# Helper functions used by web/{build.py, buildTest.py}. Could probably find a better place for them.

from devon.tags import *
import devon.make, sys

def buildProcess(request, action):
    # For some reason, Firefox ignores CSS files unless we pause before entering the build phase
    if sys.platform == "win32":
        import time
        time.sleep(0.1)
    
    request << Header(level=1) << "Building..." << Close << Flush

    if "config" in request.args:
        config = request.args["config"]
    else:
        config = "debug"
    
    request << Script << "parent." << action << "Begin();" << Close
    try:
        project = request.getTargetProject()
        result = devon.make.make(project, action, request.out, config)
            
        request << Script << "parent." << action << "End();" << Close
    except:
        request << Script << "parent." << action << "End();" << Close
        raise

    if result == 0:
        request << Block("resultBox result-success") << "Success" << Close
    else:
        request << Block("resultBox result-failure") << "Errors occurred" << Close

# **************************************************************************************************
        
class PipeBrokenError(Exception):
    pass

class ProcessBlockingError(Exception):
    def __init__(self, pid):
        self.pid = pid
