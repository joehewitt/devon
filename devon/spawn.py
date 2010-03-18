
import os, sys

# **************************************************************************************************

class SpawnPty:
    """Spawns a long running process and reads its output from a virtual terminal
    
       This is a condensed version of Noah Spurrier's Pexpect script
           http://pexpect.sourceforge.net/
    """
    
    def __init__(self, command):
        self.args = self._split_command_line(command)
        self.command = self.args[0]
        self.exitStatus = -1
        
        try:
            self.pid, self.child_fd = pty.fork()
        except OSError, e:
            raise Exception("Unable to fork")
        
        if self.pid == 0:
            self.child_fd = sys.stdout.fileno()
            os.execvp(self.command, self.args)
    
    def __del__(self):
        os.close(self.child_fd)
    
    def kill(self):
        if self.isalive():
            os.kill(self.pid, signal.SIGKILL)
    
    def isalive(self):     
        pid, status = os.waitpid(self.pid, os.WNOHANG)
        if pid == 0 and status == 0:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            
            if pid == 0 and status == 0:
                return 1

        if os.WIFEXITED(status):
            self.exitStatus = os.WEXITSTATUS(status)
            return 0
        if os.WIFSTOPPED(status):
            return 0
        if os.WIFSIGNALED(status):
            return 0

        return 0 # Can I ever get here?
            
    def read(self):        
        r, w, e = select.select([self.child_fd], [], [], 30)
        if not r:
            return ""
        
        if self.child_fd in r:
            try:
                txt = os.read(self.child_fd, 1000)
            except OSError:  # XXXblake Not sure why this happens on Unix
                txt = ""
            return txt

    def _split_command_line(self, command_line):
        """This splits a command line into a list of arguments.
        It splits arguments on spaces, but handles
        embedded quotes, doublequotes, and escaped characters.
        It's impossible to do this with a regular expression, so
        I wrote a little state machine to parse the command line.
        """
        arg_list = []
        arg = ''
        state_quote = 0
        state_doublequote = 0
        state_esc = 0
        for c in command_line:
            if c == '\\': # Escape the next character
                state_esc = 1
            elif c == r"'": # Handle single quote
                if state_esc:
                    state_esc = 0
                elif not state_quote:
                    state_quote = 1
                else:
                    state_quote = 0
            elif c == r'"': # Handle double quote
                if state_esc:
                    state_esc = 0
                elif not state_doublequote:
                    state_doublequote = 1
                else:
                    state_doublequote = 0
    
            # Add arg to arg_list unless in some other state.
            elif c == ' 'and not state_quote and not state_doublequote and not state_esc:
                if arg != '':
                    arg_list.append(arg)
                arg = ''
            else:
                arg = arg + c
                if c != '\\'and state_esc: # escape mode lasts for one character.
                    state_esc = 0
    
        # Handle last argument.        
        if arg != '':
            arg_list.append(arg)
        
        return arg_list

# **************************************************************************************************

class SpawnPopen:
    """Spawns a long running process and reads its output from a file stream.
        
        This is necessary on Windows where the pty module doesn't exist.
    """
    
    def __init__(self, command):
        self.out = os.popen4(command, "b")[1]
        self.buf = ""
        self.exitStatus = -1
        self.pid = 0
        
    def kill(self):
        # XXX Implement me!
        pass
    
    def isalive(self):
        if self.exitStatus >= 0:
            return False
            
        try:
            text = self.out.read(20)
        except:
            self.exitStatus = self.out.close()
            
            # Python returns None on success. Translate that to zero.
            if self.exitStatus is None:
                self.exitStatus = 0
                
            return False
        
        if text:                        
            self.buf += text
            return True
        
        self.exitStatus = self.out.close()

        # Python returns None on success. Translate that to zero.
        # XXXblake Merge with above
        if self.exitStatus is None:
            self.exitStatus = 0

        return False
            
    def read(self):
        self.isalive()
        text = self.buf
        self.buf = ""
        return text

# **************************************************************************************************

if sys.platform == "win32":
    Spawn = SpawnPopen
else:
    import pty, select, signal
    Spawn = SpawnPty
    
