#ifndef DEVON_LOG_H
#define DEVON_LOG_H

// Devon
#include <Devon/Loggable.h>
#include "DevonMutex.h"

// STL
#include <string>
#include <sstream>
#include <ostream>
#include <vector>
#include <map>

// We don't include Windows.h here because of all the conflicts it causes
// (e.g. it renames GetMessage to GetMessageW, conflicting with exceptions, and
// it defines many of the JSS token types)

#if defined(_WIN64)
 typedef unsigned __int64 ULONG_PTR;
#else
 typedef unsigned long ULONG_PTR;
#endif

namespace Devon {

class LogCategory;
class LogCommand;
class LogEvent;
class LogPop;
class LogLock;
class StringLog;

// ************************************************************************************************

std::string CleanTypeIdName(const std::string& typeName);

// ************************************************************************************************

class Log
{
public:
    static Log& GetRootLog();
    static Log& GetStringLog();

    enum EscapeMode
    {
        EscapeNone,
        EscapeXML,
        EscapeJS
    };
    
public:
    Log(std::ostream& stream, const std::string& name="");

    const std::string& GetName() const;
    
    bool GetDisabled() const;

    // Not guaranteed to be accurate at time of receipt due to multithreadedness.
    unsigned int GetCategoryCount() const;

    LogCategory* GetCategory(unsigned int index) const;
    void AddCategory(LogCategory& category);
    void RemoveCategory(LogCategory& category);

    Log& operator<<(long text);
    Log& operator<<(unsigned long text);
    Log& operator<<(long long text);
    Log& operator<<(unsigned long long text);
    Log& operator<<(bool text);
    Log& operator<<(short text);
    Log& operator<<(unsigned short text);
    Log& operator<<(int text);
    Log& operator<<(unsigned int text);
    Log& operator<<(float text);
    Log& operator<<(double text);    
    Log& operator<<(const char text);
    Log& operator<<(char* text);
    Log& operator<<(const char* text);
    Log& operator<<(wchar_t* text);
    Log& operator<<(const wchar_t* text);
    Log& operator<<(const void* text);
    Log& operator<<(void* text);
    Log& operator<<(const std::string& text);
    Log& operator<<(const std::wstring& text);

    Log& operator<<(EscapeMode escapeMode);

    Log& operator<<(Log& log);

    Log& operator<<(const LogCategory& category);

    Log& operator<<(const LogCommand& command);

    Log& operator<<(const LogEvent& event);

    Log& operator<<(const LogPop& pop);
        
    Log& operator<<(const LogLock& lock);

    template <typename TObject>
    void Write(const TObject* object)
    {
        if (GetDisabled())
            return;
        
        if (object)
        {
            std::string typeName = typeid(*object).name();
            std::string label = std::string("(")  + CleanTypeIdName(typeName) + ") ";
            *this << label;
            
            const TObject& ref = *object;
            Loggable<TObject>::Write(*this, ref);
        }
        else
            *this << "(NULL)";
    }

    void Subscribe(const std::string& name);

    std::string Unsubscribe(const std::string& name);

protected:
    typedef std::map<std::string, StringLog*> CollectorMap;
    
protected:
    void WriteEscapedString(const char* text, unsigned int textSize);
    
    std::ostream& mStream;
    std::string mName;
    
    // The list of all categories registered with this log
    std::vector<LogCategory*> mCategories;

    // The stack of all escape modes currently active in the logging stream
    std::vector<EscapeMode> mEscapeStack;
    
    // The stack of categories currently active in the logging stream
    std::vector<const LogCategory*> mCategoryStack;

    CollectorMap mCollectors;
    
    StringLog* mCollector;
    StringLog* mBuffer;

    // XXXblake Disable logging or this lock for release builds and performance testing.
    DevonMutex mContainerMutex;
    DevonMutex mWriteMutex;
    unsigned int mWriteLockCount;
    pthread_t mOwnerThread;
    bool mIsOwned;
};

template <typename TObject>
Log& operator<<(Log& log, TObject* object)
{
    if (object)
        log.Write(object);
    return log;
}

template <typename TObject>
Log& operator<<(Log& log, const TObject* object)
{
    if (object)
        log.Write(object);
    return log;
}

template <typename TObject>
Log& operator<<(Log& log, const TObject& object)
{
    log.Write(&object);
    return log;
}

template <typename TObject>
Log& operator<<(Log& log, const TObject** object)
{
    while (*object)
    {
        log << *object << ", ";
        ++object;
    }

    return log;
}

template <typename T>
void
Loggable<T>::Write(Log& log, const T& object)
{
#ifdef WIN32
#define PTR ULONG_PTR
#else
#define PTR uintptr_t
#endif
    log << "[" << (PTR)&object << "]";
}

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_LOG_H

