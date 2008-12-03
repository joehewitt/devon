
from devon.tags import *
import os.path, re

# **************************************************************************************************

class CLParser:
    def __init__(self):
        patterns = r"""
            (?P<Problem>^(.*?)\((\d*?)\)\s:\s(warning|error|fatal\serror)\s.*?:\s(.*?)$)
        """

        self.patterns = re.compile(patterns, re.M | re.VERBOSE)

    # XXXblake Need to fix this to output entire error message
    def parse(self, text, project, out):
        # The first line of output from CL is just the name of the file - pointless, we ignore it
        text = text[text.find("\n")+1:]
        
        m = self.patterns.search(text)
        if not m:      
            if text:
                # Print the raw text if there is no pattern match
                out << CodeBlock << text << Close << Flush

        else:
            # Find the appropriate handler to pretty print the matched text
            while m:
                groupdict = m.groupdict()
                groups = m.groups()
                offset = m.end()
                
                for name in groupdict:
                    if groupdict[name]:
                        handler = globals()["print%s" % name]
                        if handler:
                            index = self.patterns.groupindex[name]
                            handler(groups[index:], project, out)
                            out.flush()
                            break
                            
                m = self.patterns.search(text, offset)
    
            out << Flush

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *


def printProblem(m, project, out):
    message = m[3]
    
    if m[2] == "error":
        rowType = "primary"
    else:
        rowType = "secondary"
        
    out << Block("problemBox problem-%s" % m[2]) \
            << FileLink(basePath=project.path, path=m[0], lineNo=m[1], rowType=rowType) \
                << "%s (line %s)" % (m[0], m[1]) \
            << Close \
            << ":" << Span("buildMessage") << message << Close \
        << Close

# **************************************************************************************************
