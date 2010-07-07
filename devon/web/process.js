
var testStack = [];
var resultStack = [];
var gScrollInterval = setInterval(scrollToBottom, 10);
var gScrollMax = 0;

// *************************************************************************************************

//var t1 = new Date().getTime();

function onLoad(event)
{
    scrollToBottom();
    clearInterval(gScrollInterval);
    //alert(new Date().getTime()-t1);
}
window.addEventListener("load", onLoad, false);

// *************************************************************************************************
// Object Management

function objectCreated(id, typeName)
{
}

function objectDestroyed(id)
{
}

// *************************************************************************************************
// Unit Tests

function getCurrentTestName()
{
    return testStack.join("/");
}

function beginTest(name)
{
    testStack.push(name);
    resultStack.push("passed");
    
    var fullName = getCurrentTestName();
    parent.setRunningTestItem(fullName);
}

function assertionFailed()
{
    if (resultStack.length)
        resultStack[resultStack.length-1] = "failed";
}

function contractFailed()
{
}

function testExceptionThrown()
{
    if (resultStack.length)
        resultStack[resultStack.length-1] = "exception";
}

function exceptionThrown()
{
}

function endTest()
{
    var result = resultStack.pop();

    if (result != "passed")
        resultStack[resultStack.length-1] = "failed";
        
    var fullName = getCurrentTestName();
    parent.setTestStatus(fullName, result);

    testStack.pop();

    var fullName = getCurrentTestName();
    parent.setRunningTestItem(fullName);
}

// *************************************************************************************************

function scrollToBottom()
{
    // Only auto-scroll if we have grown past our previous height, to prevent from fighting
    // against the user if they try to scroll up
    //console.log(document.body.scrollHeight + " > " + gScrollMax);
    if (document.body.scrollHeight > gScrollMax)
    {
        gScrollMax = document.body.scrollHeight;
        window.scrollTo(window.scrollX, document.body.scrollHeight);
    }
}
