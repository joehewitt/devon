
import devon.web
import os.path

# **************************************************************************************************

def escapeText(text):
    text = text.replace("\n", "\\n")
    text = text.replace("\r", "\\r")
    return text
    
def main(request):
    nextEvent = devon.web.waitForUserEvent()
    
    eventText = escapeText(nextEvent)
    
    request.serveText(eventText)
