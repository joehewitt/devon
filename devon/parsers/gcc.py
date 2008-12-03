
from devon.tags import *
import os.path, re

# **************************************************************************************************

reExtraLine = re.compile(r"\s\s\s(.*?)\n")

# **************************************************************************************************

class GCCParser:
    def __init__(self):
        patterns = r"""
            (?P<Include>^In file included from (.*?):(\d*?),$)|
            (?P<From>^\s*?from\s(.+?):(\d*?):$)|
            (?P<Unknown>^g\+\+:\s(.+?):\s(.+?)$)|
            (?P<Unknown2>^(.+?):(\d+?):(\d+?):\s(.+?)$)|
            (?P<Problem>^([^\s]*?):(\d*?):\s(warning|error|note):\s(.*?)$)
        """

        self.patterns = re.compile(patterns, re.M | re.VERBOSE)

    def parse(self, text, project, out):
        m = self.patterns.search(text)
        if not m:      
            if text:
                # Print the raw text if there is no pattern match
                out << Block("log") << text << Close << Flush

        else:
            # Find the appropriate handler to pretty print the matched text
            while m:
                groupdict = m.groupdict()
                groups = m.groups()
                offset = m.end()
                
                for name in groupdict:
                    if groupdict[name]:
                        extras = ""
                        m2 = reExtraLine.match(text, offset+1)
                        while m2:   
                            extras += m2.groups()[0]
                            offset = m2.end()
                            m2 = reExtraLine.match(text, offset)
                            
                        handler = globals()["print%s" % name]
                        if handler:
                            index = self.patterns.groupindex[name]
                            handler(groups[index:], extras, project, out)
                            out.flush()
                            
                m = self.patterns.search(text, offset)

            out << Flush

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def printInclude(m, extras, project, out):
    fileName = os.path.basename(m[0])
    out << Block("problemBox problem-error") \
            << Span("problemMessage") << "File included from: " << Close \
            << FileLink("problemLink", basePath=project.path, path=m[0], lineNo=m[1]) << \
                "In %s (line %s)" % (fileName, m[1]) \
            << Close \
        << Close

def printFrom(m, extras, project, out):
    fileName = os.path.basename(m[0])
    out << Block("problemBox problem-error") \
            << Span("problemMessage") << message << Close \
            << FileLink("problemLink", basePath=project.path, path=m[0], lineNo=m[1], rowType=rowType) \
                << "From %s (line %s)" % (fileName, m[1]) \
            << Close \
        << Close

def printProblem(m, extras, project, out):
    fileName = os.path.basename(m[0])
    message = m[3] + extras
    
    if m[2] == "error":
        rowType = "primary"
    else:
        rowType = "secondary"
        
    out << Block("problemBox problem-%s" % m[2]) \
            << Span("problemMessage") << message << Close \
            << FileLink("problemLink", basePath=project.path, path=m[0], lineNo=m[1], rowType=rowType) \
                << "%s (line %s)" % (fileName, m[1]) \
            << Close \
        << Close

def printUnknown(m, extras, project, out):
    fileName = os.path.basename(m[0])
    out << Block("problemBox problem-error") \
            << Span("problemMessage") << m[1] << Close \
            << FileLink("problemLink", basePath=project.path, path=m[0], rowType="primary") \
                << fileName \
            << Close \
        << Close

def printUnknown2(m, extras, project, out):
    fileName = os.path.basename(m[0])
    message = m[3] + extras

    out << Block("problemBox problem-error") \
            << Span("problemMessage") << message << Close \
            << FileLink("problemLink", basePath=project.path, path=m[0], lineNo=m[1], rowType="primary") \
                << "%s (line %s)" % (fileName, m[1]) \
            << Close \
        << Close

# **************************************************************************************************
