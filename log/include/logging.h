#ifndef DEVON_LOGGING_H
#define DEVON_LOGGING_H

// Devon
#include <Devon/Log.h>
#include <Devon/LogCategory.h>
#include <Devon/LogCommand.h>
#include <Devon/LogEvent.h>
#include <Devon/LogPop.h>
#include <Devon/LogLock.h>
#include <Devon/StringLog.h>

namespace Devon {

// *************************************************************************************************

#define DEFAULT_LOG ::Devon::Log::GetRootLog()
#define STRING_LOG ::Devon::Log::GetStringLog()

/**
 * Re-define CURRENT_LOG to change the target log for a section of your code
 */
#define CURRENT_LOG DEFAULT_LOG

#define MESSAGE_CATEGORY ::Devon::LogCategoryDefault
#define ERROR_CATEGORY ::Devon::LogCategoryDefault
#define EXCEPTION_CATEGORY ::Devon::LogCategoryException
#define LIFETIME_CATEGORY ::Devon::LogCategoryLifetime

// *************************************************************************************************
// Logging Commmands

#define LOG_COMMAND(_NAME, _ATTRS) \
    ::Devon::LogCommand(_NAME) << _ATTRS << ::Devon::LogEndCommand

#define ATTR(_NAME, _VALUE) \
    " " << #_NAME << "=\"" << \
        ::Devon::Log::EscapeXML << _VALUE << ::Devon::Log::EscapeNone << "\""

// *************************************************************************************************
// Logging Fundamentals

#define LOGEX(_MESSAGE) \
    DEFAULT_LOG << ::Devon::LockLog << _MESSAGE << ::Devon::LogEnd

#define LOG_STRING(_MESSAGE) \
    ::Devon::ReleaseStringLog(static_cast< ::Devon::StringLog&>(::Devon::NewStringLog() \
        << _MESSAGE))

#define LOG(_MESSAGE) \
    LOGEX(_MESSAGE << "\n")

#define LOG_MESSAGE(_STYLE, _MESSAGE) \
    LOGEX(MESSAGE_CATEGORY << \
        LOG_COMMAND("beginBlock", ATTR(name, _STYLE)) \
            << _MESSAGE \
        << LOG_COMMAND("endBlock", ""))

#define LOG_ERROR(_MESSAGE) \
    LOGEX(ERROR_CATEGORY << _MESSAGE)

// *************************************************************************************************
// Logging Information

#define LOG_NOTE(_STYLE, _MESSAGE) \
    LOG_MESSAGE("note " _STYLE, _MESSAGE)

#define NOTE(_MESSAGE) \
    LOG_NOTE("", _MESSAGE)

#define NOTE_CREATE(_MESSAGE) \
    LOG_NOTE("create", _MESSAGE);

#define NOTE_DESTROY(_MESSAGE) \
    LOG_NOTE("destroy", _MESSAGE);

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

#define WARN(_MESSAGE) \
    LOG_MESSAGE("warn", _MESSAGE << LOG_CODE_FILE())

#define WARN_IF(_CONDITION, _MESSAGE) \
    if (_CONDITION) \
        WARN(_MESSAGE)
    
#define WARN_PY(_MESSAGE) \
    if (PyErr_Occurred()) \
    { \
        LOG_MESSAGE("warn", "Python exception: " << _MESSAGE); \
        PyErr_Print(); \
    }

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
// Logging Exceptions

#define LOG_EXCEPTION_FILE(_TITLE, _MESSAGE, _FILE, _LINE, _COLUMN) \
    LOG_ERROR(EXCEPTION_CATEGORY << LOG_COMMAND("exceptionThrown", \
            ATTR(title, _TITLE) \
            << ATTR(message, _MESSAGE) \
            << ATTR(fileName, _FILE) \
            << ATTR(line, _LINE) \
            << ATTR(column, _COLUMN)))

#define LOG_EXCEPTION_OBJECT(_EXC) \
    LOG_EXCEPTION_FILE(_EXC.GetName(), _EXC.GetMessage(), _EXC.GetFileName(), _EXC.GetLine(), \
        _EXC.GetColumn())

#define LOG_EXCEPTION(_TITLE, _MESSAGE) \
    LOG_EXCEPTION_FILE(#_TITLE, _MESSAGE, __FILE__, __LINE__, 0)

// *************************************************************************************************
// Logging Debugging

#define LOG_REACH() \
    LOGEX(LOG_COMMAND("reach", ATTR(fileName, __FILE__) << ATTR(line, __LINE__)))

#define LOG_VARIABLE(_VAR) LOGEX( \
    LOG_COMMAND("beginVariable", ATTR(name, #_VAR) << ATTR(value, (_VAR))) \
    << LOG_COMMAND("endVariable", ""))

#define LOG_VARIABLE_FORMAT(_VAR, _FORMAT) LOGEX( \
    LOG_COMMAND("beginVariable", ATTR(name, #_VAR) << ATTR(value, (_VAR))) \
        << _FORMAT(_VAR) \
    << LOG_COMMAND("endVariable", ""))

#define LOG_RAW(_TEXT) \
    LOG(LOG_COMMAND("beginRawText", "") << _TEXT << LOG_COMMAND("endRawText", ""));

// *************************************************************************************************
// Logging Text Formats

#define LOG_URL(_TEXT) \
    LOG_COMMAND("link", ATTR(href, _TEXT))

#define LOG_FILE(_PATH, _LINE) \
    LOG_COMMAND("fileLink", ATTR(fileName, _PATH) << ATTR(line, _LINE))

#define LOG_CODE_FILE() \
    LOG_COMMAND("fileLink", ATTR(fileName, __FILE__) << ATTR(line, __LINE__))

// *************************************************************************************************
// Logging Lifetimes

#define LOG_CONSTRUCTOR() \
    LOGEX(LIFETIME_CATEGORY << \
        LOG_COMMAND("constructObject", ATTR(id, (int)this) << ATTR(typeName, this)))

#define LOG_DESTRUCTOR() \
    LOGEX(LIFETIME_CATEGORY << \
        LOG_COMMAND("destroyObject", ATTR(id, (int)this) << ATTR(typeName, this)))

#define LOG_EXIT() \
    LOGEX(LOG_COMMAND("programExit", ""));

// *************************************************************************************************
// Logging Events

void IncrementSemaphore(const wchar_t* name);
void WaitOnSemaphore(const wchar_t* name, unsigned long long timeoutMs);

#define LOG_SUBSCRIBE(_NAME) \
    DEFAULT_LOG.Subscribe(_NAME);
    
#define LOG_UNSUBSCRIBE(_NAME) \
    DEFAULT_LOG.Unsubscribe(_NAME);
    
#define LOG_EVENT(_NAME, _MESSAGE) \
    ::Devon::IncrementSemaphore(_NAME); \
    LOG(::Devon::LogEvent(_NAME) << _MESSAGE)

#define LOG_WAIT(_NAME, _TIMEOUTMS) \
    ::Devon::WaitOnSemaphore(_NAME, _TIMEOUTMS);

// *************************************************************************************************
// Logging Groups

#define START(_MESSAGE) \
    LOGEX(LOG_MESSAGE("group", _MESSAGE << LOG_CODE_FILE()) \
        << LOG_COMMAND("beginBlock", ATTR(name, "indent")));

#define AUTOSTART(_MESSAGE) \
    START(_MESSAGE); \
    ::Devon::AutoStart __autostart__;

#define FINISH() \
    LOGEX(LOG_COMMAND("endBlock", ""))

class AutoStart
{
public:
    AutoStart() {}
    ~AutoStart() { FINISH(); }
};

// *************************************************************************************************
// Logging Tables

#define LOG_BEGIN_TABLE(_NAME) \
    LOGEX(LOG_COMMAND("beginTable", ATTR(name, _NAME)))

#define LOG_END_TABLE() \
    LOGEX(LOG_COMMAND("endTable", ""))   

#define LOG_BEGIN_ROW(_ROWTYPE) \
    LOGEX(LOG_COMMAND("beginRow", ATTR(rowType, _ROWTYPE)))

#define LOG_END_ROW() \
    LOGEX(LOG_COMMAND("endRow", ""))

#define LOG_CELL(_VALUE) \
    LOGEX(LOG_COMMAND("cell", ATTR(value, _VALUE)))

// *************************************************************************************************
// Shorthand for macros used often while under duress

#define dd(_TEXT) LOGEX(_TEXT);
#define ddv(_TEXT) LOG_VARIABLE(_TEXT);
#define ddf(_TEXT, _FORMAT) LOG_VARIABLE_FORMAT(_TEXT, _FORMAT);
#define bbb LOG_REACH();

// *************************************************************************************************

} // namespace Devon

#endif // DEVON_LOGGING_H
