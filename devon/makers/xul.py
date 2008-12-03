
import re, os.path

# **************************************************************************************************

reHead = re.compile(r"""(<method name="(.*?)"([^>]*)>)|(<handler ([^>]*)>)|(<constructor>)|(<destructor>)|(<property name="(.*?)"([^>]*)>)|(<getter>)|(<setter>)""", re.M)
reParam = re.compile(r"""<parameter name="(.*?)"[^>]*/>""", re.M)
reCDATA = re.compile(r"""<!\[CDATA\[((.|\n)+?)]]>""", re.M)

reFn = re.compile("function\s*(.*?)\(([^\)]*)\)[\s\n]*(\{)", re.M)

reListener = re.compile('\son.+?="(.*?)"')

reComma = re.compile(",\s?")

reScript = re.compile(r"""<script.+?src="(.+?)".*?/>""")

# **************************************************************************************************

def iterateListeners(txt):
    """Gets the set of all inline event listeners in a single XUL file."""
    
    index = 0
    while 1:
        mValue = reListener.search(txt, index)
        if not mValue:
            break
        
        yield mValue.group(1), mValue.start(1), mValue.end(1)
        index = mValue.end(1)+1

def iterateScripts(txt):
    """Gets the set of all script tags in a single XUL file.
       
       Note that this expects all script tags to be contiguous or there
       will be other non-script content in between."""

    index = 0
    scripts = []
    scriptStart = 0
    scriptEnd = 0

    while 1:
        mScript = reScript.search(txt, index)
        if not mScript:
            break
        
        if not scriptStart:
            scriptStart = mScript.start(0)
        
        scripts.append(mScript.group(1))
        scriptEnd = mScript.end(0)
        
        index = scriptEnd+1
    
    return scripts, scriptStart, scriptEnd

def iterateMembers(txt):
    """Gets the set of all XBL members in a single XBL file."""
    
    index = 0
    while 1:
        mHead = reHead.search(txt, index)
        if not mHead:
            break

        if mHead.group(1):
            index = mHead.end(1)+1
            mBody = reCDATA.search(txt, index)
            bodyStart = mBody.start(0)

            argNames = []
            while 1:
                m = reParam.search(txt, index)
                if not m:
                    break

                index = m.end(0)+1
                if index > bodyStart:
                    break

                argNames.append(m.group(1))

            yield "method", mHead.group(2), argNames, "", mBody.group(1), mHead.start(1), mBody.end(0)

            index = mBody.end(0)+1

        elif mHead.group(4):
            index = mHead.end(4)
            mBody = reCDATA.search(txt, index)

            yield "handler", "", [], mHead.group(5), mBody.group(1), mHead.start(4), mBody.end(0)

            index = mBody.start(0)+1
        
        elif mHead.group(6):
            index = mHead.end(6)
            mBody = reCDATA.search(txt, index)

            yield "constructor", "", [], "", mBody.group(1), mHead.start(6), mBody.end(0)

            index = mBody.start(0)+1
        
        elif mHead.group(7):
            index = mHead.end(7)
            mBody = reCDATA.search(txt, index)

            yield "destructor", "", [], "", mBody.group(1), mHead.start(7), mBody.end(0)

            index = mBody.start(0)+1

        elif mHead.group(8):
            index = mHead.end(8)

            yield "property", mHead.group(9), [], mHead.group(10), mBody.group(1), mHead.start(8), mHead.end(8)

            index = mHead.end(0)+1
        
        elif mHead.group(11):
            index = mHead.end(11)
            mBody = reCDATA.search(txt, index)

            yield "getter", "", [], "", mBody.group(1), mHead.start(11), mBody.end(0)

            index = mBody.start(0)+1
        
        elif mHead.group(12):
            index = mHead.end(12)
            mBody = reCDATA.search(txt, index)

            yield "setter", "", [], "", mBody.group(1), mHead.start(12), mBody.end(0)

            index = mBody.start(0)+1

def restoreMember(memberType, name, extra, params, body):
    """Re-creates an XBL member element from parts created by iterateMembers."""
    
    if memberType == "method":
        paramText = ""
        for param in params:
            paramText += """        <parameter name="%s"/>\n""" % param

        return """<method name="%s">\n%s        <body><![CDATA[%s]]>""" \
            % (name, paramText, body)
    
    elif memberType == "handler":
        return """<handler %s>\n        <![CDATA[%s]]>""" % (extra, body)

    elif memberType == "constructor":
        return """<constructor>\n        <![CDATA[%s]]>""" % (body)

    elif memberType == "destructor":
        return """<destructor>\n        <![CDATA[%s]]>""" % (body)

    elif memberType == "property":
        return """<property name="%s">""" % (name)

    elif memberType == "getter":
        return """<getter>\n        <![CDATA[%s]]>""" % (body)

    elif memberType == "setter":
        return """<setter>\n        <![CDATA[%s]]>""" % (body)

def parseFunction(txt):
    """Parse a single JavaScript function into name, arguments, and body."""
    
    m = reFn.match(txt)

    name = m.group(1)
    args = reComma.split(m.group(2))
    body = txt[m.end(3):txt.rfind("}")]

    return name, args, body
