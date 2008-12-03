
import devon.renderers.text
from devon import tags

import os.path, sys, types

# **************************************************************************************************

class OutStream:
    def __init__(self, out=None, renderer=None):
        if out:
            self.out = out
        else:
            self.out = sys.stdout
        
        if renderer:
            self.renderer = renderer
        else:
            self.renderer = devon.renderers.text.TextRenderer()

        self.tagStack = []
        
    def __lshift__(self, value):
        self.write(value)
        return self

    def __str__(self):
        if self.out.getvalue:
            return self.out.getvalue()
        else:
            return "<OutStream>"
    
    def write(self, data):
        if data == tags.Flush:
            self.flush()

        elif (type(data) is types.ClassType and issubclass(data, tags.Close)) \
                or isinstance(data, tags.Close):
            tag = self.tagStack.pop()
            
            self.renderer.renderCloseTag(tag, self.out)

        else:
            if type(data) is types.ClassType and issubclass(data, tags.Tag):
                data = data()

            if isinstance(data, tags.Tag):
                self.tagStack.append(data)

                self.renderer.renderOpenTag(data, self.out)

            else:
                self.renderer.renderText(data, self.out)

    def flush(self):
        self.out.flush()

    def getTopTag(self):
        if len(self.tagStack):
            return self.tagStack[-1]
        else:
            return None

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

def generateStrings(fn):
    """Wraps generators that yield non-string objects and converts them to a string."""
    
    def wrapper():
        for value in fn():
            yield str(value)
    
    return wrapper
