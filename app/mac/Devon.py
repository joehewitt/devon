#!/usr/bin/env python

from Foundation import *
from AppKit import *
from objc import YES, NO, nil, signature
from WebKit import *
from Carbon.CarbonEvt import RegisterEventHotKey, GetApplicationEventTarget
from devon.desktop.mac.virtualKeys import hotKeyToVirtualCodes, hotKeyToPrettyName
from devon.web import serve
from _devon_macsupport import HotKeyAddress
import os.path, sys, struct, thread

kEventHotKeyPressedSubtype = 6
kEventHotKeyReleasedSubtype = 9

defaultWindowFrame = ((100.0, 100.0), (924.0, 668.0))

devonURL = "http://localhost:3800"

def aeKeyword(fourCharCode):
	return struct.unpack('>i', fourCharCode)[0]

class DevonApp(NSApplication):
    hotKeys = {}
    commands = []
    
    def sendEvent_(self, theEvent):
        if theEvent.type() == NSSystemDefined and theEvent.subtype() == kEventHotKeyPressedSubtype:
            key, handler = self.hotKeys[theEvent.data1()]
            handler.callWebScriptMethod_withArguments_("apply", [nil, []])
            
        super(DevonApp, self).sendEvent_(theEvent)

    def postKeyEvent(self, character, modifierFlags=0):
       keyEvent = NSEvent.keyEventWithType_location_modifierFlags_timestamp_windowNumber_context_characters_charactersIgnoringModifiers_isARepeat_keyCode_(NSKeyDown, (0, 0), modifierFlags, theEvent.timestamp(), theEvent.windowNumber(), None, character, None, False, 0)
       self.postEvent_atStart_(keyEvent, True)
    
    def dispatchCommand(self, commandName, param, args):
        callArgs = []
        for key in args:
            callArgs += [key, args[key]]
            
        for name, handler in self.commands:
            if name == commandName:
                handler.callWebScriptMethod_withArguments_("apply", [nil, [param, callArgs]])
    
    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
        
    def buildAppleEvent_(self, event):
        self.dispatchCommand("build", event.directParameter(), event.evaluatedArguments())

    def cleanAppleEvent_(self, event):
        self.dispatchCommand("clean", event.directParameter(), event.evaluatedArguments())

    def runAppleEvent_(self, event):
        self.dispatchCommand("run", event.directParameter(), event.evaluatedArguments())

    def findAppleEvent_(self, event):
        self.dispatchCommand("find", event.directParameter(), event.evaluatedArguments())

    def findNextAppleEvent_(self, event):
        self.dispatchCommand("findNext", event.directParameter(), event.evaluatedArguments())

class AppDelegate(NSObject):
    initialProjectPath = None
    window = None
    webView = None
    
    def applicationDidFinishLaunching_(self, aNotification):
        win = self.window = NSWindow.alloc()
        win.initWithContentRect_styleMask_backing_defer_(((0, 0), (0, 0)),
            NSTitledWindowMask | NSClosableWindowMask
            | NSMiniaturizableWindowMask | NSResizableWindowMask,
            NSBackingStoreBuffered, YES)
        win.setTitle_("")
        win.setLevel_(NSNormalWindowLevel)

        webView = self.webView = WebView.alloc().initWithFrame_(((0.0, 0.0), (10.0, 10.0)))
        win.setContentView_(webView)
        win.setInitialFirstResponder_(webView)
        
        self.loadDelegate = LoadDelegate.alloc().init()
        webView.setFrameLoadDelegate_(self.loadDelegate)
        self.uiDelegate = UIDelegate.alloc().init()
        webView.setUIDelegate_(self.uiDelegate)
        
        if self.initialProjectPath:
            self.openProject(self.initialProjectPath)
        else:
            defaults = NSUserDefaults.standardUserDefaults()
            path = defaults.stringForKey_("devon.LastProject")
            if path:
                self.openProject(path)
            
        self.restorePosition()
        win.makeKeyAndOrderFront_(nil)
        win.makeMainWindow()
        win.setDelegate_(self)
        
    def application_openFile_(self, app, path):
        name,ext = os.path.splitext(path)
        if ext == ".dev":
            self.openProject(path)
            return YES
        else:
            return NO

    def application_openFiles_(self, app, paths):
        for path in paths:
            self.application_openFile_(app, path)
    
    def windowDidResize_(self, notification):
        self.persistPosition()

    def windowDidMove_(self, notification):
        self.persistPosition()

    def openProject(self, projectPath):
        if self.webView:
            defaults = NSUserDefaults.standardUserDefaults()
            defaults.setObject_forKey_(projectPath, "devon.LastProject")

            url = "%s/%s/" % (devonURL, projectPath.replace("/", ":"))
            request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
            self.webView.mainFrame().loadRequest_(request)
        else:
            self.initialProjectPath = projectPath
            
    def persistPosition(self):
        defaults = NSUserDefaults.standardUserDefaults()
        frame = self.window.frame()
        windowFrame = ((frame.origin.x, frame.origin.y), (frame.size.width, frame.size.height))
        defaults.setObject_forKey_(windowFrame, "devon.WindowPosition")
    
    def restorePosition(self):
        defaults = NSUserDefaults.standardUserDefaults()
        frame = defaults.arrayForKey_("devon.WindowPosition")
        if not frame:
            frame = defaultWindowFrame

        self.window.setFrame_display_(frame, YES)
        
class LoadDelegate(NSObject, protocols.WebFrameLoadDelegate):
    def webView_didFailLoadWithError_forFrame_(self, webView, error, frame):
        print "FAILED", error
        
    def webView_didFailProvisionalLoadWithError_forFrame_(self, webView, error, frame):
        print "FAILED PROVISIONAL", error

    def webView_didFinishLoadForFrame_(self, webView, frame):
        pass
        
    def webView_didClearWindowObject_forFrame_(self, webView, window, frame):
        if not frame.parentFrame():
            window.setValue_forKey_(self, "devon")

    def webView_didReceiveTitle_forFrame_(self, webView, title, frame):
        if not frame.parentFrame():
            NSApp().delegate().window.setTitle_(title)

    def isKeyExcludedFromWebScript_(self, key):
        return YES

    def isSelectorExcludedFromWebScript_(self, sel):
        if str(sel) in ["activate", "bounce", "registerHotKey", "unregisterHotKey", 
            "registerCommand", "unregisterCommand"]:
            return NO
        else:
            return YES
    
    def activate(self):
        NSApp().activateIgnoringOtherApps_(YES)

    def bounce(self, forever):
        NSApp().requestUserAttention_(NSCriticalRequest if forever else NSInformationRequest)
        
    def registerCommand(self, name, handler):
        NSApp().commands += [(name, handler)]

    def unregisterCommand(self, name, handler):
        pass
        
    def registerHotKey(self, hotKeyName, handler):
        keyCode, flags = hotKeyToVirtualCodes(hotKeyName)
        key = RegisterEventHotKey(keyCode, flags, (0, 0), GetApplicationEventTarget(), 0)

        app = DevonApp.sharedApplication()
        app.hotKeys[HotKeyAddress(key)] = (key, handler)

    def unregisterHotKey(self, hotKeyName, handler):
        app = DevonApp.sharedApplication()
        for address in app.hotKeys:
            key, theHandler = app.hotKeys[address]
            if handler == theHandler:
                key.UnregisterEventHotKey()

class UIDelegate(NSObject, protocols.WebUIDelegate):
    def webView_runJavaScriptAlertPanelWithMessage_initiatedByFrame_(self, webView, message, frame):
        print message
    
def main():
    thread.start_new_thread(serve, ())
    
    app = DevonApp.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()    

if __name__ == '__main__':
    print "LAUNCHING..."
    main()
