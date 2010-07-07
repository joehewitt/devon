
var building = 0;
var runningPid = 0;
var runningItem = null;

// *************************************************************************************************

function onLoadProcess(event)
{
    var processBody = document.getElementById("process").contentWindow;
    processBody.addEventListener("keydown", onKeyDown, true);
}

function onResize(event)
{
    layoutHBox();
}
window.addEventListener("resize", onResize, false);

function onKeyDown(event)
{
    if (event.keyCode == 70 && event.shiftKey && event.metaKey)
    {
        focusFind();
        event.preventDefault();
        event.stopPropagation();
    }
}

function initialize()
{
    addEventListener("keydown", onKeyDown, true);

    document.getElementById("process").addEventListener("load", onLoadProcess, true);

    document.getElementById("tabBar").addEventListener("click", onClickTab, false);
    document.getElementById("tabBox").addEventListener("click", onClickTabBox, false);

    showTab("projects");
    setTimeout(layoutHBox, 100);
    
    setTimeout(listenForEvents, 100);
}

function loadURL(url)
{
    document.getElementById("process").src = url;
}

// *************************************************************************************************
// Event Listener

function listenForEvents()
{
    //loadXMLData("./eventListen:", "", onUserEvent);
}

function onUserEvent(result)
{
    setTimeout(listenForEvents, 0);
}

// *************************************************************************************************
// Process callbacks

function buildBegin()
{
    building = true;
    document.getElementById("build").firstChild.nodeValue = "Cancel";
}

function buildTestsBegin()
{
    building = true;
    document.getElementById("buildTests").firstChild.nodeValue = "Cancel";
}

function buildEnd()
{
    building = false;
    document.getElementById("build").firstChild.nodeValue = "Build";
}

function buildTestsEnd()
{
    building = false;
    document.getElementById("buildTests").firstChild.nodeValue = "Tests";
}

function runBegin(pid)
{
    runningPid = pid;
    
    document.getElementById("runKill").firstChild.nodeValue = "Stop";
}

function runEnd(pid)
{
    if (runningPid == pid)
    {
        runningPid = 0;
     
        document.getElementById("runKill").firstChild.nodeValue = "Run";
    }
}

// *************************************************************************************************

function onFocusFind()
{
    var findBox = document.getElementById("findBox");
    if (findBox.value == "Find in project")
        findBox.value = "";
    else
        findBox.select()
}

function onBlurFind()
{
    var findBox = document.getElementById("findBox");
    if (findBox.value == "")
        findBox.value = "Find in project";
}

function submitFind(replace)
{
    var findPath = getSelectedProjectPath();
    
    var findBox = document.getElementById("findBox");
    var terms = escape(findBox.value);
    var url = "./find:" + findPath + "?terms=" + terms;

    if (replace)
    {
        var replaceBox = document.getElementById("replaceBox");
        url += "&replaceTerms=" + replaceBox.value;
    }
    
    var typesBox = document.getElementById("typesBox");
    if (typesBox.value)
        url += "&fileTypes=" + typesBox.value;

    var typesBox = document.getElementById("typesBox");
    if (document.getElementById("findCase").checked)
        url += "&caseSensitive=true";

    window.frames[0].location = url;
}

function onFindKeypress(event)
{
    if (event.keyCode == 13)
        submitFind();
}

function toggleFindMenu()
{
    var findMenu = document.getElementById("findMenu");
    if (findMenu.style.display == "block")
    {
        findMenu.style.display = "none";
    }
    else
    {
        findMenu.style.display = "block";
    }
}

function toggleReplace()
{
    var replaceOn = document.getElementById("replaceOn");
    var replaceBox = document.getElementById("replaceBox");
    if (replaceOn.checked)
    {
        replaceBox.disabled = false;
    }
    else
    {
        replaceBox.disabled = true;
    }
}

// *************************************************************************************************

function onURLBarKeyPress(event)
{
    if (event.keyCode == 13)
    {
        var browser = document.getElementById("browser");
        var urlBox = document.getElementById("urlBox");
        if (urlBox.value.length)
            browser.src = urlBox.value;
    }
}

// *************************************************************************************************

function toggleBar(name)
{
    var button = document.getElementById(name + "Button");
    toggleState(button, "toggled");
    var bar = document.getElementById(name + "Bar");
    toggleDisplay(bar);

    var splitter = getNextElement(bar);
    if (splitter && hasState(splitter, "splitter"))
        toggleDisplay(splitter);        

    splitter = getPreviousElement(bar);
    if (splitter && hasState(splitter, "splitter"))
        toggleDisplay(splitter);        

    layoutHBox();
}

function showTab(name)
{
    var tab = document.getElementById(name + "Tab");
    var tabBar = document.getElementById("tabBar");
    var selectedTab = findNextWithState(tabBar, "selected");
    var tabBox = document.getElementById(name + "Box");

    if (tab && tab != selectedTab)
    {
        if (selectedTab)
            removeState(selectedTab, "selected");
    
        setState(tab, "selected");
        
        showTabBox(name);
    }
    
    if (!tabBox.firstChild)
        refreshTab(name);
}

function refreshTab(name)
{
    if (name == "projects")
        loadCatalog("projectCatalog", "projects", createHeader);

    else if (name == "logs")
        loadCatalog("logCatalog", "logs", createLogCheckbox);

    else if (name == "tests")
        loadCatalog("testCatalog", "tests", createHeader);

}

function showTabBox(name)
{
    var box = document.getElementById(name + "Box");
    var tabBox = document.getElementById("tabBox");
    var selectedBox = findChildWithState(tabBox, "selected");

    if (box && box != selectedBox)
    {
        if (selectedBox)
            removeState(selectedBox, "selected");
    
        setState(box, "selected");
    }
}

function onClickTab(event)
{
    if (event.detail == 2)
    {
        var id = event.target.id;
        var name = id.substr(0, id.length-3);
        refreshTab(name);
    }
}

function onClickTabBox(event)
{
    if (event.target.nodeName == "A")
        return;

    var tabBox = document.getElementById("tabBox");
    var treeBox = findChildWithState(tabBox, "selected");

    selectTreeItem(treeBox, null);
}

function onMouseDownTreeItem(event)
{
    var tabBox = document.getElementById("tabBox");
    var treeBox = walkUp(tabBox, event.target);
    var item = this.parentNode.parentNode;

    selectTreeItem(treeBox, item);

    // Don't focus link, which causes the list to scroll horizontally if the label is long
    event.preventDefault();
}

function selectTreeItem(treeBox, item)
{
    if (treeBox.selectedItem)
        removeState(treeBox.selectedItem, "selected");
    
    treeBox.selectedItem = item;
    
    if (item)
    {
        setState(item, "selected");
        
        var testName = getTestItemName(item);
        if (testName)
        {
            var processDoc = document.getElementById("process").contentDocument;
            var headerElt = processDoc.getElementById("testBegin-" + testName);
            if (headerElt)
                headerElt.scrollIntoView();
        }    
    }
}

// *************************************************************************************************

function layoutHBox()
{
    var hbox = document.getElementById("hbox");
    if (!hbox)
        return;

    var flexCount = 0;
    var availWidth = hbox.clientWidth - 2;
    var child = hbox.firstChild;
    while (child)
    {
        if (child.nodeType == 1)
        {
            if (child.hasAttribute("flex"))
                ++flexCount;
            else
                availWidth -= child.clientWidth;
        }
        child = child.nextSibling;
    }

    child = hbox.firstChild;
    while (child)
    {
        if (child.nodeType == 1)
        {
            if (child.hasAttribute("flex"))
                child.style.width = (availWidth/flexCount) + "px";
        }
        child = child.nextSibling;
    }

    var x = 0;
    child = hbox.firstChild;
    while (child)
    {
        if (child.nodeType == 1)
        {
            child.style.left = x + "px";
            x += child.offsetWidth;
        }
        child = child.nextSibling;
    }
    
}

// *************************************************************************************************

function onMouseDownSplitter(event)
{
    top.movingSplitter = event.target;
    top.movingLeft = getPreviousElement(top.movingSplitter);
    top.movingRight = getNextElement(top.movingSplitter);
    top.movingX = event.clientX;
    top.movingLeftX = top.movingSplitter.offsetLeft;
    top.movingLeftWidth = top.movingLeft.clientWidth;
    top.movingRightWidth = top.movingRight.clientWidth;

    window.addEventListener("mousemove", onMouseMoveSplitter, true);
    window.addEventListener("mouseup", onMouseUpSplitter, true);
    
    for (var i = 0; i < window.frames.length; ++i)
    {
        window.frames[i].addEventListener("mousemove", onMouseMoveSplitterFrame, true);
        window.frames[i].addEventListener("mouseup", onMouseUpSplitter, true);
    }
    
    event.preventDefault();
}

function onMouseMoveSplitter(event)
{
    updateSplitter(event.clientX);
}

function onMouseMoveSplitterFrame(event)
{
    var xCheat = 0;
    if (isDocumentInFrames(top.movingLeft, event.target.ownerDocument))
        xCheat = top.movingLeft.offsetLeft;
    else if (isDocumentInFrames(top.movingRight, event.target.ownerDocument))
        xCheat = top.movingRight.offsetLeft;

    updateSplitter(xCheat + event.clientX);
}

function onMouseUpSplitter(event)
{
    window.removeEventListener("mousemove", onMouseMoveSplitter, true);
    window.removeEventListener("mouseup", onMouseDownSplitter, true);

    for (var i = 0; i < window.frames.length; ++i)
    {
        window.frames[i].removeEventListener("mousemove", onMouseMoveSplitterFrame, true);
        window.frames[i].removeEventListener("mouseup", onMouseUpSplitter, true);
    }
}

function updateSplitter(offsetX)
{
    var xDiff = offsetX - top.movingX;

    top.movingLeft.style.width = (top.movingLeftWidth + xDiff) + "px";
    top.movingRight.style.width = (top.movingRightWidth - xDiff) + "px";

    layoutHBox();
}

function isDocumentInFrames(root, doc)
{
    if (root.nodeName == "IFRAME" && doc == root.contentDocument)
        return true;
        
    var iframes = root.getElementsByTagName("IFRAME");
    for (var i in iframes)
        if (doc == iframes[i].contentDocument)
            return true;
    return false;
}

// *************************************************************************************************

function loadCatalog(catalogName, tabName, itemCreator)
{
    showTabBox("loading");
    
    loadXMLData("./" + catalogName + ":", "", 
        function(data)
        {
            var tabBox = document.getElementById(tabName+"Box");
            removeAllChildren(tabBox);

            for (var i in data)
                itemCreator(data[i], tabBox);
                
            showTabBox(tabName);
        },
        function (error, message)
        {
            showTabBox(tabName);
            //alert("Unable to load the catalog.");
        }
    );
}

function createHeader(data, tabBox)
{
    var itemDiv = document.createElement("div");
    itemDiv.className = "treeHeader";
    itemDiv.setAttribute("testId", data.id);

    var linkElt = document.createElement("a");
    linkElt.href = "#";
    linkElt.className = "treeItemLink";
    linkElt.addEventListener("mousedown", onMouseDownTreeItem, false);
    linkElt.appendChild(document.createTextNode(data.name));

    var spanElt = document.createElement("span");
    spanElt.className = "treeItemBox";
    spanElt.appendChild(linkElt);

    itemDiv.appendChild(spanElt);
    tabBox.appendChild(itemDiv);
    
    var bodyDiv = document.createElement("div");
    bodyDiv.className = "treeBody";
    tabBox.appendChild(bodyDiv);

    for (var i in data.children)
        createTestItem(data.children[i], bodyDiv, data.id);
}

function createLogCheckbox(data, tabBox)
{
    if (data.type == "project")
    {
        var itemDiv = document.createElement("div");
        itemDiv.className = "treeHeader";
    
        var linkElt = document.createElement("a");
        linkElt.href = "#";
        linkElt.className = "treeItemLink";
        linkElt.appendChild(document.createTextNode(data.name));
    
        var spanElt = document.createElement("span");
        spanElt.className = "treeItemBox";
        spanElt.appendChild(linkElt);
    
        itemDiv.appendChild(spanElt);
        tabBox.appendChild(itemDiv);
    }
    else
    {
        var li = document.createElement("li");
        li.className = "treeItem treeItemCheckbox";
        
        var cbElt = document.createElement("input");
        cbElt.type = "checkbox";
        cbElt.logName = data.name;
        if (!data.disabled)
            cbElt.checked = true;
            
        var linkElt = document.createElement("a");
        linkElt.href = "#";
        linkElt.className = "treeItemLink";
        linkElt.addEventListener("mousedown", onMouseDownTreeItem, false);
        linkElt.appendChild(document.createTextNode(data.name));
    
        var spanElt = document.createElement("span");
        spanElt.className = "treeItemBox";
        spanElt.appendChild(linkElt);
    
        li.appendChild(cbElt);
        li.appendChild(spanElt);
        tabBox.appendChild(li);
    }
}

function createTestItem(data, parent, parentId)
{
    var fullId = parentId ? parentId + "/" + data.id : data.id;
    
    var li = document.createElement("li");
    li.className = "treeItem";
    li.id = "test-" + fullId;
    li.setAttribute("testId", data.keepId ? data.id : fullId);
    if (data.testStatus)
        li.setAttribute("testStatus", data.testStatus);
    
    var linkElt = document.createElement("a");
    linkElt.href = "#";
    linkElt.className = "treeItemLink treeItemType-" + data.itemType;
    linkElt.addEventListener("mousedown", onMouseDownTreeItem, false);
    linkElt.appendChild(document.createTextNode(data.name));

    var spanElt = document.createElement("span");
    spanElt.className = "treeItemBox";
    spanElt.appendChild(linkElt);

    li.appendChild(spanElt);
    parent.appendChild(li);

    if (data.children.length)
    {
        li.className += " treeBranch";
        
        var ul = document.createElement("ul");
        ul.className = "treeList";
        parent.appendChild(ul);
        
        for (var i in data.children)
            createTestItem(data.children[i], ul, fullId);
    }
}

function setRunningTestItem(name)
{
    if (name) {
        var item = document.getElementById("test-" + name);
        if (item) {
            if (runningItem)
                removeState(runningItem, "running");
            runningItem = item;
            setState(item, "running");
        }
        
    } else {
        if (runningItem) {
            removeState(runningItem, "running");
            runningItem = null;
        }
    }
}

function addClass(elt, className) {
    var classes = elt.className.split(" ");
    classes.push(className);
    elt.className = classes.join(" ");
}

function removeClass(elt, className) {
    var classes = elt.className.split(" ");
    classes.remove(className);
    elt.className = classes.join(" ");
}

function removeClassWithPrefix(elt, prefix) {
    var classes = elt.className.split(" ");
    for (var cls in classes) {
        if (cls.indexOf(prefix) == 0) {
            classes.remove(cls);
        }
    }
    elt.className = classes.join(" ");
}

function setTestStatus(name, status)
{
    var rowElt = document.getElementById("test-" + name);
    if (rowElt) {
        removeClassWithPrefix(rowElt, 'testStatus-')
        addClass(rowElt, 'testStatus-' + status);
    }
}

function getTestItemName(item)
{
    return item.id && item.id.indexOf("test-") == 0
        ? item.id.substr(5)
        : null;
}

function getSelectedTestId()
{
    var tree = document.getElementById("testsBox");
    return tree.selectedItem
        ? tree.selectedItem.getAttribute("testId")
        : null;
}

function getSelectedProjectPath()
{
    var tree = document.getElementById("projectsBox");
    return tree.selectedItem
        ? tree.selectedItem.getAttribute("testId")
        : "";
}

function resetAllTestItemStatus()
{
    var tree = document.getElementById("testsBox");
    function criteria(node) { return node.nodeType == 1 && node.nodeName == "LI"; }
    var node = findNode(tree.firstChild, criteria, tree);
    while (node)
    {
        if (node.getAttribute("testStatus") != "skip")
            node.removeAttribute("testStatus");
        node = findNode(node.firstChild, criteria, tree);
    }
}
