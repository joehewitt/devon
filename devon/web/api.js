
var focusedLink = null;

function process(processName)
{
    if ((processName == "build" || processName == "buildTests") && building)
        cancelBuild();
    else if (processName == "run" && runningPid)
        cancelRun();
    else if (processName == "dist")
        loadURL("/build:" + getSelectedProjectPath() + "?config=release");
    else if (processName == "run")
        run(false);
    else if (processName == "debug")
        run(true);
    else if (processName == "browse")
        reloadBrowser();
    else
        loadURL("/" + processName + ":" + getSelectedProjectPath());
}

function edit(basePath, filePath, line, col1, col2)
{
    var url = "/edit:" + filePath.replace("../", "", "g");
    if (line != undefined)
    {
        url += "?line=" + line + "&basePath=" + basePath;

        if (col1 != undefined && col2 != undefined)
            url +=  "&col1=" + col1 + "&col2=" + col2;
    }
    
    var req = createXMLHttpRequest();
    req.open("GET", url, true);
    req.send("");
}

function shutdown()
{
    var url = "/shutdown:";
    var req = createXMLHttpRequest();
    req.open("GET", url, true);
    req.send("");
}

function cancelBuild()
{
    if (!building)
        return;

    var url = "/buildStop:";
    var req = createXMLHttpRequest();
    req.open("GET", url, true);
    req.send("");
}

function run(debugMode)
{
    resetAllTestItemStatus();

    var testId = getSelectedTestId();
    if (testId)
        loadURL("/run:" + projectPath + "?target=" + testId + "&disabledLogs=" + 
            "&debugger=" + debugMode);
    else
        loadURL("/run:" + projectPath + "?disabledLogs=" +
            "&debugger=" + debugMode);
}

function cancelRun()
{
    if (!runningPid)
        return;

    var url = "/kill:?pid=" + runningPid;
    var req = createXMLHttpRequest();
    req.open("GET", url, true);
    req.send("");

    runEnd(runningPid);
}

function focusFind()
{
    var findBox = document.getElementById("findBox");
    findBox.focus();
}

function doFind(terms)
{
    var findBox = document.getElementById("findBox");
    findBox.value = terms;
    findBox.focus();
    findBox.select();
    if (terms)
        submitFind();
}

function findNextLink()
{
    var processDoc = document.getElementById("process").contentDocument;
    
    function criteria(node)
    {
        return node.nodeType == 1
            && node.nodeName.toUpperCase() == "A"
            && node.getAttribute("rowType") == "primary";
    }
    
    //var focusedLink = processDoc.defaultView.getSelection().focusNode;

    var currentLink = focusedLink && focusedLink.ownerDocument == processDoc
            && criteria(focusedLink)
        ? focusedLink.firstChild
        : processDoc.body;

    focusedLink = findNode(currentLink, criteria);
    if (focusedLink)
    {
        focusedLink.focus();
        var href = unescape(focusedLink.href);
        eval(href.substr(11));
    }
}

function reloadBrowser()
{
// XXXjoe I'm not sure if I want to always show the browser or not
//    var button = document.getElementById("browserButton");
//    if (!hasState(button, "toggled"))
//        toggleBar("browser");

    var browser = document.getElementById("browser");
    var urlBox = document.getElementById("urlBox");
    if (urlBox.value.length)
        browser.src = urlBox.value;
}

function printfire()
{
    if (document.createEvent)
    {
        printfire.args = arguments;
        var ev = document.createEvent("Events");
        ev.initEvent("printfire", false, true);
        dispatchEvent(ev);
    }
}