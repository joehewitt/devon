
import devon.renderers, devon.stream
from devon import tags
import cStringIO

# **************************************************************************************************

# TODO: Add option - width of view in characters
# TODO: Add option - show links as urls or bracketed
# TODO: Add option - show structure classes or not
# TODO: Add option - show style classes or not

class TextRenderer(devon.renderers.Renderer):
    def __init__(self, lineWidth=100):
        self.rendererStack = []
    
    def getRendererForTag(self, tag):
        if tag.__class__ in textTagRenderers:
            return textTagRenderers[tag.__class__]
        
        for baseClass in tag.__class__.__bases__:
            if baseClass in textTagRenderers:
                return textTagRenderers[baseClass]

    def getTopRenderer(self):
        if len(self.rendererStack):
            return self.rendererStack[-1]
        else:
            return None

    def renderOpenTag(self, tag, out):
        renderer = self.getRendererForTag(tag)
        self.rendererStack.append(renderer)
        if renderer:
            renderer.renderOpenTag(tag, out)

    def renderCloseTag(self, tag, out):
        renderer = self.rendererStack.pop()
        if renderer:
            renderer.renderCloseTag(tag, out)

    def renderText(self, text, out):
        renderer = self.getTopRenderer()
        if renderer:
            renderer.renderText(text, out)
        else:
            out.write(text)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class NodeRenderer(devon.renderers.Renderer):    
    def __init__(self, textBefore=None, textAfter=None):
        self.textBefore = textBefore
        self.textAfter = textAfter

    def renderOpenTag(self, tag, out):
        pass
        
    def renderCloseTag(self, tag, out):
        pass

    def renderText(self, text, out):
        out.write(text)

    def getTextBefore(self, tag):
        if callable(self.textBefore):
            return self.textBefore(self, tag)
        else:
            return self.textBefore

    def getTextAfter(self, tag):
        if callable(self.textAfter):
            return self.textAfter(self, tag)
        else:
            return self.textAfter

class Block(NodeRenderer):    
    def renderCloseTag(self, tag, out):
        out.write("\n")
        if self.textAfter:
            out.write(self.getTextAfter(tag))

class LineBlock(Block): pass

class NextLineBlock(Block):        
    def renderOpenTag(self, tag, out):
        if self.textBefore:
            out.write(self.getTextBefore(tag) + "\n")
        
    def renderText(self, text, out):
        out.write(text)

class Span(NodeRenderer):
    def renderOpenTag(self, tag, out):
        if self.textBefore:
            out.write(self.getTextBefore(tag))
        
    def renderCloseTag(self, tag, out):
        if self.textAfter:
            out.write(self.getTextAfter(tag))

class Link(NodeRenderer):
    def renderOpenTag(self, tag, out):
        out.write("[[")
        if "href" in tag.attributes:
            out.write(tag.attributes["href"])
        if "title" in tag.attributes:
            out.write("|" + tag.attributes["title"])

    def renderCloseTag(self, tag, out):
        out.write("]]")

    def renderText(self, text, out):
        pass

class FileLink(NodeRenderer):
    def renderOpenTag(self, tag, out):
        pass
        
    def renderCloseTag(self, tag, out):
        pass

    def renderText(self, text, out):
        out.write(text)

class EmptyBlock(NodeRenderer):
    def renderText(self, text, out):
        pass

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def mapHeaderTagLineChar(renderer, tag):
    char = "="
    return char * (100/len(char))

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

textTagRenderers = {
    tags.Tag: None,
    
    tags.Block: Block(),

    tags.Paragraph: Block(),

    tags.Section: None,
    
    tags.Header: NextLineBlock(mapHeaderTagLineChar, "\n"),

    tags.Separator: LineBlock("_"),

    tags.QuoteBlock: Block("`\n"),

    tags.CodeBlock: Block("`\n"),

    tags.Script: EmptyBlock(),

    tags.Style: EmptyBlock(),

    tags.Span: Span(),

    tags.Emph: Span("*", "*"),

    tags.Strong: Span("_", "_"),

    tags.Code: Span("`", "`"),
    
    tags.Link: Link(),
    
    tags.FileLink: FileLink(),

    tags.Image: None,
    
    tags.Anchor: None,
    
    tags.Field: None,
   
    tags.OrderedList: None,

    tags.UnorderedList: None,

    tags.ListItem: Block("* "),

    tags.Table: None,

    tags.Row: None,

    tags.Cell: None,

    tags.HTMLTag: None
}

# **************************************************************************************************

def createTextStream(out=None):
    if not out:
        out = cStringIO.StringIO()

    renderer = devon.renderers.text.TextRenderer()
    return devon.stream.OutStream(out, renderer)
