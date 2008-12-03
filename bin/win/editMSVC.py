
import win32com.client, sys

# **************************************************************************************************

def editFile(path, line=-1, col1=-1, col2=-1):
    path = path.replace("/", "\\") # MSVC can't handle forward slashes
    try:
        app = win32com.client.Dispatch("VisualStudio.DTE")

        # The only way to bring a window to the foreground (anything else just flashes the taskbar)
        # win32gui.SetForegroundWindow(app.MainWindow.HWnd)
        
        # Ensure that the IDE remains open after automation if we opened it
        # app.UserControl = True
        
        # We should be using app.OpenFile here, but that doesn't ensure that the case of the path is
        # correct. This results in the following aggravating problem: VS gives us lowercase paths in
        # its messages. We pass those paths to OpenFile, and VS opens the file as lowercase. When
        # the file is then edited and saved, the case of the file is changed. The indirection below
        # works around that.
        app.ExecuteCommand("File.OpenFile " + path)
        
        # app.MainWindow.Visible = True
        
        if line >= 0:
            doc = app.ActiveDocument # None
            # path = path.lower()
            # for i in xrange(1, app.Documents.Count+1):
            #    print app.Documents(i).FullName.lower()
            #    if app.Documents(i).FullName.lower() == path:
            #        doc = app.Documents(i)
            #        break
            
            if col1 > 0 and col2 > 0:
                doc.Selection.MoveToLineAndOffset(line, col1)
                doc.Selection.MoveToLineAndOffset(line, col2, 1)
            else:
                doc.Selection.GoToLine(line)

    except:
        print "Unable to edit file '%s' in Visual Studio" % path
        raise

# **************************************************************************************************

path = sys.argv[1]

if len(sys.argv) >= 5:
    col1 = int(sys.argv[3])
    col2 = int(sys.argv[4])
else:
    col1 = -1
    col2 = -1
    
if len(sys.argv) > 2:
    line = int(sys.argv[2])
else:
    line = -1

editFile(path, line, col1, col2)


