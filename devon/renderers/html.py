
import devon.renderers, devon.stream
from devon import tags
import os.path, re, cStringIO

# **************************************************************************************************

class HTMLRenderer(devon.renderers.Renderer):
    def __init__(self):
        self.rendererStack = []
    
    def getRendererForTag(self, tag):
        if tag.__class__ in htmlTagRenderers:
            return htmlTagRenderers[tag.__class__]
        
        for baseClass in tag.__class__.__bases__:
            if baseClass in htmlTagRenderers:
                return htmlTagRenderers[baseClass]

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

class HTMLElement(devon.renderers.Renderer):    
    def __init__(self, nodeName, classes=None, **attributes):
        self.nodeName = nodeName

        if classes:
            attributes["class"] = classes
        self.attributes = attributes        

    def renderOpenTag(self, tag, out):
        if callable(self.nodeName):
            nodeName = self.nodeName(self, tag)
        else:
            nodeName = self.nodeName
            
        out.write("<%s" % nodeName)
            
        attributes = self.translateAttributes(tag)
        if attributes:
            for name in attributes:
                value = attributes[name]
                if not callable(value):
                    out.write(' %s="%s"' % (name, escapeHTMLText(value)))

        out.write(">")

    def renderCloseTag(self, tag, out):
        if callable(self.nodeName):
            nodeName = self.nodeName(self, tag)
        else:
            nodeName = self.nodeName

        out.write("</%s>" % nodeName)

    def renderText(self, text, out):
        out.write(escapeHTMLText(text))

    def translateAttributes(self, tag):
        newAttributes = {}

        if tag.attributes:
            newAttributes.update(tag.attributes)

        for name in self.attributes:
            value = self.attributes[name]
            if not callable(value):
                if name == "class":
                     # class is a special case - append it to the existing class
                     mergeClass(newAttributes, value)
                else:
                    newAttributes[name] = value
                    
            else:
                # Call the filter and expect it to return a dictionary of attributes
                translatedAttributes = value(tag, name)
                if translatedAttributes:
                    # Merge the filtered attributes with the current attributes
                    for newName in translatedAttributes:
                        newValue = translatedAttributes[newName]
                        if newValue:
                            if newName == "class":
                                # class is a special case - append it to the existing class
                                mergeClass(newAttributes, newValue)
                            else:
                                newAttributes[newName] = newValue
                
        return newAttributes
        
class HTMLCommentedElement(HTMLElement):
    def renderText(self, text, out):
        out.write(text)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def mapHeaderTagNodeName(self, tag):
    if "level" in tag.attributes:
        return "h%s" % tag.attributes["level"]

def mapHTMLTagNodeName(self, tag):
    return tag.nodeName

class MapAttribute:
    def __init__(self, name=None, defaultValue=None, filter=None):
        self.name = name
        self.filter = filter
        self.defaultValue = defaultValue
    
    def __call__(self, tag, name):
        if tag.attributes and self.name in tag.attributes:
            value = tag.attributes[self.name]
            if self.filter:
                return self.filter(tag, name, value)
            else:
                return {name: value}
        else:
            return {name: self.defaultValue}

reAbsoluteURL = re.compile(r"[a-zA-Z]\w*://")
def canonizeURL(tag, name, url):
    if not reAbsoluteURL.match(url):
        url = url.replace(" ", "_")
        url = "/" + url

    return {name: url}

def getEditorURL(tag, name, path):
    basePath = ""
    lineNo = 0
    colNo1 = 0
    colNo2 = 0

    if "basePath" in tag.attributes:
        basePath = tag.attributes["basePath"]
    if "lineNo" in tag.attributes:
        lineNo = tag.attributes["lineNo"]
    if "colNo1" in tag.attributes:
        colNo1 = tag.attributes["colNo1"]
    if "colNo2" in tag.attributes:
        colNo2 = tag.attributes["colNo2"]

    escapedBasePath = basePath.replace("\\", "/")
    escapedPath = path.replace("\\", "/")

    return {name: "javascript: parent.edit('%s', '%s', %s, %s, %s);" \
        % (escapedBasePath, escapedPath, lineNo, colNo1, colNo2)}
    
def getBubbleURL(tag, name, text):
    return {name: "javascript: bubble('%s')" % text}
    
def getFootnoteURL(tag, name, text):
    return {name: "#%s" % text}
    
def getCitationURL(tag, name, text):
    return {name: "#%s" % text}
    
def getListItemType(tag, name, value):
    if value == "o":
        return {"type": "circle"}
    elif value == "-":
        return {"type": "square"}
    elif value == "x":
        return {"classes": "bullet-x-sm"}
    elif value == "X":
        return {"classes": "bullet-x-lg"}
    elif value >= "a" and value <= "z":
        return {"type": "a"}
    elif value >= "A" and value <= "Z":
        return {"type": "A"}

def escapeHTMLText(text):
    if not isinstance(text, basestring):
        text = str(text)
        
    # XXX Slow - regular expressions would be better no?
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text

def mergeClass(attributes, classes):
    if "class" in attributes and attributes["class"]:
        attributes["class"] += " " + classes
    else:
        attributes["class"] = classes

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

htmlTagRenderers = {
    tags.Tag: None,

    tags.Block: HTMLElement("div"),
    
    tags.Paragraph: HTMLElement("p"),

    tags.Section: None,

    tags.Header: HTMLElement(mapHeaderTagNodeName),

    tags.Separator: HTMLElement("hr"),

    tags.QuoteBlock: HTMLElement("blockquote"),

    tags.CodeBlock: HTMLElement("pre", classes="code"),

    tags.Script: HTMLCommentedElement("script", language="Javascript"),

    tags.Style: HTMLCommentedElement("style", type="text/css"),

    tags.Span: HTMLElement("span"),

    tags.Emph: HTMLElement("em"),

    tags.Strong: HTMLElement("strong"),

    tags.Code: HTMLElement("code"),
    
    tags.Link: HTMLElement("a"),

    tags.FileLink: HTMLElement("a", href=MapAttribute("path", filter=getEditorURL)),

    tags.Image: HTMLElement("img", src=MapAttribute("src")),
    
    tags.Anchor: None,
    
    tags.Field: None,
    
    tags.TextArea: HTMLElement("textarea"),
    
    tags.OrderedList: HTMLElement("ol"),

    tags.UnorderedList: HTMLElement("ul"),

    tags.ListItem: HTMLElement("li", type=MapAttribute("listType", filter=getListItemType)),

    tags.Table: HTMLElement("table"),

    tags.Row: HTMLElement("tr"),

    tags.Cell: HTMLElement("td"),

    tags.HTMLTag: HTMLElement(mapHTMLTagNodeName),   
}

# **************************************************************************************************

def createHTMLStream(out=None):
    if not out:
        out = cStringIO.StringIO()
        
    renderer = devon.renderers.html.HTMLRenderer()
    return devon.stream.OutStream(out, renderer)
