
// *************************************************************************************************
// XML Loading

function loadXMLData(url, args, resultCallback, errorCallback)
{ 
    var req = createXMLHttpRequest();
    if (!req)
        errorCallback(-1, "");
    
    req.onreadystatechange = function(event)
    {
        if (req.readyState == 4)
        {
            var result = undefined;
            try {
                if (req.status == 200)
                    result = eval(req.responseText);
            } catch (ex) {
                if (errorCallback)
                    errorCallback(ex);
            }
            
            resultCallback(result);

            // Prevent leak, cut circular reference
            req.onreadystatechange = null;
        }
    };

    req.open("GET", url + "?" + args, true);
    req.send(null);
    return req;
}
    
function createXMLHttpRequest()
{
    var prefixes = ["MSXML2", "Microsoft", "MSXML", "MSXML3"];
    for (var i = 0; i < prefixes.length; i++)
    {
        try {
            return new ActiveXObject(prefixes[i] + ".XmlHttp");
        } catch (ex) { }
    }

    try {
        return new XMLHttpRequest();
    } catch (ex) { }
    
    return null;
}
// ************************************************************************************************
// Node Searching

function walkUp(parent, node)
{
    while (node && node.parentNode != parent)
        node = node.parentNode;
    return node;
}

function findNode(node, criteria, container)
{
    while (node)
    {
        if (criteria(node))
            return node;

        node = findNext(node, container);
    }
    
    return null;
}

function findNext(node, container)
{
    var next = node.firstChild;
    if (next)
        return next;
        
    while (node && node != container)
    {
        next = node.nextSibling;
        if (next)
            return next;
        
        node = node.parentNode;
    }
    return null;
}

function findNextWithState(root, state)
{
    function finder(node) { return node.nodeType == 1 && hasState(node, state); }
    return findNode(root, finder, root);
}

function findChildWithState(root, state)
{
    function finder(node) { return node.nodeType == 1 && hasState(node, state); }
    var node = root.firstChild;
    while (node && !finder(node))
        node = node.nextSibling;
    return node;
}

function getNextElement(node)
{
    node = node.nextSibling;
    while (node && node.nodeType != 1)
        node = node.nextSibling;
    return node;
}

function getPreviousElement(node)
{
    node = node.previousSibling;
    while (node && node.nodeType != 1)
        node = node.previousSibling;
    return node;
}

function toggleDisplay(node)
{
    if (node.style.display == "none")
        node.style.display = "block";
    else
        node.style.display = "none";
}

// ************************************************************************************************
// States

function hasState(node, name)
{
    return node.className.indexOf(name) != -1;
}

function setState(node, name)
{
    node.className += " " + name;
}

function removeState(node, name)
{
    var index = node.className.indexOf(name);
    var size = name.length;
    node.className = node.className.substr(0,index-1) + node.className.substr(index+size);
}

function toggleState(node, name)
{
    if (hasState(node, name))
        removeState(node, name);
    else
        setState(node, name);
}

function removeAllChildren(node)
{
    var child = node.lastChild;
    while (child)
    {
        var prev = child.previousSibling;
        node.removeChild(child);
        child = prev;
    }
}
