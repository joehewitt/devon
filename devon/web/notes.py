
from devon.tags import *

import devon.projects, devon.wiki.db
import os.path

# **************************************************************************************************

def main(request):
    request.servePage("wiki.html", globals(), locals())

def renderPage(request):
    db = devon.wiki.db.WikiDatabase(request.project)
    db.sync()
    
    notesPath = os.path.abspath(os.path.join(request.project.path, request.project.wikiPath,
        request.path))
    
    if "tag" in request.args:
        renderTags(request, db, notesPath, request.args["tag"])
    else:
        renderDocuments(request, db, notesPath)

    renderTagBox(request, db)
    
def renderTags(request, db, notesPath, tagName):
    wikiPath = os.path.abspath(os.path.join(request.project.path, request.project.wikiPath))
    
    document = None

    for tagName,fileId,chapterId,line in db.getTagReferences(tagName):
        if not document or not document.id == fileId:
            if document:
                request << Close

            document = db.getDocument(fileId)
            
            wikiName = getWikiName(document.path, wikiPath)
            documentName = getWikiTitle(document.path, wikiPath)

            request \
                << Block << Link("pageLink", href=wikiName, path=document.path) \
                    << documentName \
                << Close << Close \
                << UnorderedList
        
        chapter = db.getSection(chapterId)
        request \
            << ListItem << Link("chapterLink", href=wikiName, path=document.path,
                                lineNo=chapter.line+1) \
                << os.path.basename(chapter.name) \
            << Close
        
        for tagName in db.getTagNamesBySection(chapterId):
            request << Link("tagLink", href="/notes:%s?tag=%s" % (request.path, tagName)) \
                << "[%s]" % tagName << Close << " "
            
        request << Close
    
    if document:
        request << Close
    
def renderDocuments(request, db, notesPath):
    wikiPath = os.path.abspath(os.path.join(request.project.path, request.project.wikiPath))

    for document in db.getDocumentsByPath(notesPath):
        wikiName = getWikiName(document.path, wikiPath)
        documentName = getWikiTitle(document.path, wikiPath)
        
        request \
            << Block << Link("pageLink", href=wikiName, path=document.path) \
                << documentName \
            << Close << Close

        chapterStack = []
        
        for chapter in db.getSectionsByDocument(document.path):
            if len(chapterStack):
                if chapter.level < chapterStack[-1].level:
                    while len(chapterStack) and chapter.level <= chapterStack[-1].level:
                        if chapter.level < chapterStack[-1].level:
                            request << Close
                        chapterStack.pop()

                elif chapter.level == chapterStack[-1].level:
                    chapterStack.pop()

                elif chapter.level > chapterStack[-1].level:
                    request << OrderedList
            else:
                request << OrderedList

            chapterStack.append(chapter)
            
            request \
                << ListItem \
                    << Link("chapterLink", href=wikiName, path=document.path,
                                    lineNo=chapter.line+1) \
                        << os.path.basename(chapter.name) \
                    << Close
            
            for tagName in db.getTagNamesBySection(chapter.id):
                request << Link("tagLink", href="/notes:%s?tag=%s" % (request.path, tagName)) \
                    << "[%s]" % tagName << Close << " "
                
            request << Close
        
        for chapter in chapterStack:
            request << Close

def renderTagBox(request, db):
    request << Block("tagBox")
    
    for tagName, count in db.getTagNames():
        if count == 1:
            tagSize = "1"
        elif count < 5:
            tagSize = "2"
        elif count < 10:
            tagSize = "3"
        else:
            tagsize = "4"
        
        request \
            << Link("tagLink tagSize%s" % tagSize, href="/notes:%s?tag=%s" \
                    % (request.path, tagName)) << tagName << Close
    
    request << Close

def getWikiName(pagePath, wikiPath):
    pathIndex = pagePath.find(wikiPath)
    return "/" + os.path.splitext(pagePath[len(wikiPath)+1:])[0]
    
def getWikiTitle(pagePath, wikiPath):
    pathIndex = pagePath.find(wikiPath)
    names = os.path.splitext(pagePath[len(wikiPath)+1:])[0]
    return names.replace("/", " > ")
    
    