
# **************************************************************************************************

class Node:
    def __init__(self, attributes=None):
        self.attributes = attributes
        self.childNodes = None
    
    def __getitem__(self, name):
        return self.attributes[name]
    
    def __setitem__(self, name, value):
        self.attributes[name] = value
    
    def __lshift__(self, value):
        from devon.stream import OutStream
        from devon.renderers.html import HTMLRenderer
        from cStringIO import StringIO
        
        stream = OutStream(StringIO(), HTMLRenderer())
        stream.write(self)
        stream.write(value)
        return stream

    def clone(self):
        cloned = self.__class__(self.line)
        cloned.mergeAttributes(self.attributes)
        return cloned

    def mergeAttributes(self, attributes):
        if self.attributes:
            self.attributes.update(attributes)
        else:
            self.attributes = dict(attributes)

    def appendChild(self, node):
        if not self.childNodes:
            self.childNodes = []
        
        self.childNodes.append(node)

    def getInnerText(self):
        text = ""
        if self.childNodes:
            for node in self.childNodes:
                if isinstance(node, basestring):
                    text += node
        
        return text
        
    def iterateNodes(self, exclude=None):
        if self.childNodes:
            for node in self.childNodes:
                if exclude and exclude(node):
                    continue
                    
                yield node
    
                if isinstance(node, Node):
                    if node.childNodes:
                        for child in node.iterateNodes(exclude):
                            yield child

                    yield Close

    def getNodesBy(self, criteria):
        if self.childNodes:
            for node in self.childNodes:
                if isinstance(node, Node) and node.childNodes:
                    if criteria(node):
                        yield node
    
                    for child in node.getNodesBy(criteria):
                        yield child

    def __str__(self):
        xml = "<%s" % self.__class__.__name__
        if self.attributes:
            for name in self.attributes:
                xml += ' %s="%s"' % (name, self.attributes[name])
        xml += ">"

        return xml
        
# **************************************************************************************************
    
class Document(Node):
    def __init__(self, sourcePath=None):
        self.sourcePath = sourcePath
        Node.__init__(self)

# **************************************************************************************************

class Tag(Node):
    def __init__(self, classes=None, line=-1, **attributes):
        self.line = line

        if classes:
            attributes["class"] = classes

        Node.__init__(self, attributes)

    def clone(self):
        cloned = self.__class__("", self.line)
        cloned.mergeAttributes(self.attributes)
        return cloned

# **************************************************************************************************

class Close:
    """Write this class to the stream to close the last open tag."""

    def __init__(self, line=-1):
        self.line = line

class Flush:
    """Write this class to the stream to flush all buffered text."""

class FileTarget:
    def getFileTargetPath(self):
        pass

# **************************************************************************************************

def dumpNodeTree(node, out=None, indent=""):
    if not out:
        import sys
        out = sys.stdout
        
    out.write(indent)
    if isinstance(node, basestring):
        out.write("'" + node + "'\n")
    else:
        out.write(str(node) + "\n")

    if isinstance(node, Node) and node.childNodes:
        childIndent = indent + "    "
        for child in node.childNodes:
            dumpNodeTree(child, out, childIndent)

        out.write(indent)
        out.write("</%s>\n" % node.__class__.__name__)

