
from devon.tag import Tag
from devon.tag import Close
from devon.tag import Flush
from devon.tag import FileTarget

import types

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
        
class Block(Tag): pass

class Paragraph(Block): pass

class Section(Block): pass

class Header(Block): pass

class Separator(Block): pass

class QuoteBlock(Block): pass
        
class CodeBlock(Block): pass

class Script(Block): pass

class Style(Block): pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class Span(Tag): pass

class Emph(Span): pass

class Strong(Span): pass

class Code(Span): pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class Image(Span): pass

class Link(Span): pass

class FileLink(Span, FileTarget):
    def getFileTargetPath(self):
        if "path" in self.attributes:
            return self["path"]

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class Anchor(Span): pass

class AnchorTag(Anchor): pass

class AnchorId(Anchor): pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class Field(Tag): pass

class TextArea(Tag): pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class List(Tag): pass

class OrderedList(List): pass

class UnorderedList(List): pass

class ListItem(Block): pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class Table(Tag): pass

class Row(Tag): pass

class Cell(Block): pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class HTMLTag(Tag):
    def __init__(self, nodeName, classes=None, line=-1, **attributes):
        self.nodeName = nodeName

        Tag.__init__(self, classes, line, **attributes)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def isCloseTag(node):
    return (type(node) is types.ClassType and issubclass(node, Close)) \
        or isinstance(node, Close)
