// Devon
#include <Devon/Log.h>
#include <Devon/LogCategory.h>
#include <Devon/LogCommand.h>
#include <Devon/LogEvent.h>
#include <Devon/LogPop.h>
#include <Devon/LogLock.h>
#include <Devon/StringLog.h>

// STL
#include <algorithm>
#include <fstream>

namespace Devon {

// *************************************************************************************************
// Globals

LogCategory LogCategoryDefault("Default");
LogCategory LogCategoryAssertion("Assertions");
LogCategory LogCategoryException("Exceptions");
LogCategory LogCategoryLifetime("Lifetimes");

LogPop LogEnd;
LogPop LogEndCommand;

LogLock LockLog;

// *************************************************************************************************
// Local Constants

static const char* kBeginMessage = "\x001";
static const char* kEndMessage = "\x002";

static StringLog* kDeadCollector = reinterpret_cast<StringLog*>(0xFFFFFFFF);

#ifdef WIN32
static const char* kLogFilePath = "c:/temp/DevonLog.txt";
static const char* kDisabledLogsFilePath = "c:/temp/DevonDisabledLogs.txt";
#else
static const char* kLogFilePath = "/tmp/DevonLog.txt";
static const char* kDisabledLogsFilePath = "/tmp/DevonDisabledLogs.txt";
#endif

// *************************************************************************************************
// Local Helpers

inline bool
isNumber(char s)
{
    return s >= '0' && s <= '9';
}

inline bool
isNotNumber(char s)
{
    return !(s >= '0' && s <= '9');
}

static std::vector<std::string>&
GetDisabledCategories()
{
    static std::vector<std::string> disabledCategories;
    return disabledCategories;
}

static bool
IsCategoryDisabled(const std::string& name)
{
    static std::vector<std::string>& disabledCategories = GetDisabledCategories();

    return std::find(disabledCategories.begin(), disabledCategories.end(), name) != 
        disabledCategories.end();
}

// *************************************************************************************************
// Global Helpers

std::string
CleanTypeIdName(const std::string& typeName)
{
    // C++ doesn't specify the format of a typeid name. MSVC formats its typeids as "class <name>",
    // with no angle brackets. GCC has its own weird format, which looks something like
    // "N6Devon4DomainE".  I don't know what the N or E mean, perhaps "namespace" and "end"? Anyway,
    // the numbers refer to the length of each segment of the string.  This little bit here just
    // parses the string and turns it into something like "Devon::Domain".
    // (XXXblake This will fail for identifiers that contain numbers.)

#ifdef WIN32
    // Just strip out the "class" prefix
    return typeName.substr(6);
#endif

    std::string cleanName = "";
    
    std::string::const_iterator iter = typeName.begin();
    std::string::const_iterator iterEnd = typeName.end();
    while (iter != iterEnd)
    {
        std::string::const_iterator firstNum = std::find_if(iter, iterEnd, isNumber);
        if (firstNum == iterEnd)
            break;
        
        std::string::const_iterator firstNonNum = std::find_if(firstNum, iterEnd, isNotNumber);
        if (firstNonNum == iterEnd)
            break;
    
        std::string charCountStr = std::string(firstNum, firstNonNum);
        unsigned int charCount = atoi(charCountStr.c_str());
        
        iter = firstNonNum+charCount;
        
        if (!cleanName.empty())
            cleanName += "::";
        
        cleanName += std::string(firstNonNum, iter);
    }
    
    return cleanName;
}

// *************************************************************************************************
// Log class public

Log::Log(std::ostream& stream, const std::string& name)
    :   mStream(stream),
        mName(name),
        mCollector(NULL),
        mWriteLockCount(0),
        mIsOwned(false)
{
    static std::vector<std::string>& disabledCategories = GetDisabledCategories();

    char categoryName[1024];
    
    static std::ifstream GetDisabledLogsStream(kDisabledLogsFilePath);
    while (GetDisabledLogsStream.good())
    {
        GetDisabledLogsStream.getline(categoryName, 1024);
        if (::strlen(categoryName) > 0)
            disabledCategories.push_back(categoryName);
    }
}

Log&
Log::GetRootLog()
{
    // Purposely leak the log because we need it to remain alive up until the very last
    // nanosecond, even after the main function, because there may be other global or
    // static variables that wish to use the log in their destructors, and there is no
    // way to predict which order these are destroyed
    static std::ofstream* logStream = new std::ofstream(kLogFilePath, std::ios::app);
    static Log* log = new Log(*logStream, "Default Log");
    return *log;
}

Log&
Log::GetStringLog()
{
    static StringLog stringLog;
    return stringLog;
}

const std::string&
Log::GetName() const
{
    return mName;
}

bool
Log::GetDisabled() const
{
    AutoDevonMutex autoMutex(const_cast<DevonMutex*>(&mContainerMutex));
    if (mCollector == kDeadCollector)
        return true;
    else if (mCategoryStack.empty())
        return false;
    else
    {
        const LogCategory* category = mCategoryStack.back();
        return category->GetDisabled();
    }
}

unsigned int
Log::GetCategoryCount() const
{
    return mCategories.size();
}

LogCategory*
Log::GetCategory(unsigned int index) const
{
    return mCategories[index];
}

void
Log::AddCategory(LogCategory& category)
{
    if (IsCategoryDisabled(category.GetName()))
        category.SetDisabled(true);
    else
        category.SetDisabled(false);

    AutoDevonMutex autoMutex(mContainerMutex); 
    mCategories.push_back(&category);
}

void
Log::RemoveCategory(LogCategory& category)
{
    AutoDevonMutex autoMutex(mContainerMutex);
    mCategories.erase(std::remove(mCategories.begin(), mCategories.end(), &category));
}

Log&
Log::operator<<(long text)
{
    if (GetDisabled())
        return *this;
   
    // Not sure why the explicit cast is required on msvc. --Blake
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(unsigned long text)
{
    if (GetDisabled())
        return *this;

    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(long long text)
{
    if (GetDisabled())
        return *this;
        
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(unsigned long long text)
{
    if (GetDisabled())
        return *this;
    
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(bool text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(short text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(unsigned short text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(int text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(unsigned int text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(float text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(double text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(const char text)
{
    if (GetDisabled())
        return *this;
   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(char* text)
{
    return operator<<(const_cast<const char*>(text));
}

Log&
Log::operator<<(const char* text)
{
    if (GetDisabled())
        return *this;
   
    if (text)
        WriteEscapedString(text, strlen(text));
    else
        *this << "(NULL)";

    return *this;
}

Log&
Log::operator<<(wchar_t* text)
{
    // This function is necessary because msvc defers to the generic operator<<
    // when you use a non-const wchar_t*. -Blake
    return operator<<(const_cast<const wchar_t*>(text));
}

Log&
Log::operator<<(const wchar_t* text)
{
    if (GetDisabled())
        return *this;
   
    size_t len = wcslen(text);
    char* buf = new char[len + 1];
    wcstombs(buf, text, len + 1);
    
    if (text)
        WriteEscapedString(buf, len);
    else
        *this << "(NULL)";

    delete[] buf;

    return *this;
}

Log&
Log::operator<<(const void* text)
{
    if (GetDisabled())
        return *this;
 
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    stream << text;
    return *this;
}

Log&
Log::operator<<(void* text)
{
    // This function is necessary because msvc defers to the generic operator<<
    // when you use a non-const void* (which is what win32 HANDLEs are.) -Blake
    return operator<<(const_cast<const void*>(text));
}

Log&
Log::operator<<(const std::string& text)
{
    if (GetDisabled())
        return *this;

    WriteEscapedString(text.c_str(), text.size());
    
    return *this;
}

Log&
Log::operator<<(const std::wstring& text)
{
    return *this << text.c_str();
}

Log&
Log::operator<<(Log::EscapeMode escapeMode)
{  
    AutoDevonMutex autoMutex(mContainerMutex);

    if (escapeMode == EscapeNone)
        mEscapeStack.pop_back();
    else
        mEscapeStack.push_back(escapeMode);
    return *this;
}

Log&
Log::operator<<(Log& log)
{
    return log;
}

Log&
Log::operator<<(const LogCategory& category)
{  
    AutoDevonMutex autoMutex(mContainerMutex);

//    if (&category == &LogCategoryEnd)
//        mCategoryStack.pop_back();
//    else
        mCategoryStack.push_back(&category);
    return *this;
}

Log&
Log::operator<<(const LogCommand& command)
{
    if (GetDisabled())
        return *this;
  
    mStream.seekp(0, std::ios_base::end);
    mStream << kBeginMessage << "<" << command.GetName();
    return *this;
}

Log&
Log::operator<<(const LogEvent& event)
{
    if (GetDisabled())
        return *this;
  
    AutoDevonMutex autoMutex(mContainerMutex);

    const std::string eventName = event.GetName();
    CollectorMap::const_iterator iter = mCollectors.find(eventName);
    if (iter != mCollectors.end())
        mCollector = iter->second;
    else
        mCollector = kDeadCollector;
    
    return *this;
}

Log&
Log::operator<<(const LogPop& pop)
{   
    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    if (&pop == &LogEndCommand)
        *this << "/>" << kEndMessage;
    else if (&pop == &LogEnd)
    {
        AutoDevonMutex autoMutex(mContainerMutex);

        mCategoryStack.clear();
        mCollector = NULL;

        if (mIsOwned && pthread_equal(pthread_self(), mOwnerThread) && --mWriteLockCount == 0)
        {
            mIsOwned = false;
            mWriteMutex.Unlock();
        }
    }

    stream.flush();
    
    return *this;
}

Log&
Log::operator<<(const LogLock& lock)
{
    pthread_t id = pthread_self();
    if (!mIsOwned || !pthread_equal(id, mOwnerThread))
    {
        mWriteMutex.Lock();
        mOwnerThread = id;
        mIsOwned = true;
    }

    ++mWriteLockCount;
    return *this;
}

void
Log::Subscribe(const std::string& name)
{   
    StringLog* log = new StringLog();

    AutoDevonMutex autoMutex(mContainerMutex);

    mCollectors[name] = log;
}

std::string
Log::Unsubscribe(const std::string& name)
{   
    AutoDevonMutex autoMutex(mContainerMutex);

    CollectorMap::const_iterator iter = mCollectors.find(name);
    if (iter != mCollectors.end())
    {
        std::string value = iter->second->GetString();

        delete iter->second;
        mCollectors[name] = NULL;
        
        return value;
    }
    else
        return "";
}

// *************************************************************************************************
// Log class protected

void
Log::WriteEscapedString(const char* text, unsigned int textSize)
{   
    AutoDevonMutex autoMutex(mContainerMutex);

    std::ostream& stream = mCollector ? (std::ostream&)mCollector->GetStream() : mStream;

    if (!mEscapeStack.empty())
    {
        if (mEscapeStack.back() == EscapeXML)
        {
            const char* c = text;
            const char* lastWrite = c;
            const char* maxBytes = c + textSize;
            for (c; *c != 0 && c < maxBytes; ++c)
            {
                if (*c == '"')
                {
                    stream.write(lastWrite, c-lastWrite);
                    stream << "&quot;";
                    lastWrite = c+1;
                }
                else if (*c == '&')
                {
                    stream.write(lastWrite, c-lastWrite);
                    stream << "&amp;";
                    lastWrite = c+1;
                }
                else if (*c == '<')
                {
                    stream.write(lastWrite, c-lastWrite);
                    stream << "&lt;";
                    lastWrite = c+1;
                }
                else if (*c == '>')
                {
                    stream.write(lastWrite, c-lastWrite);
                    stream << "&gt;";
                    lastWrite = c+1;
                }
                else if (*c == '\n')
                {
                    stream.write(lastWrite, c-lastWrite);
                    stream << "\\n";
                    lastWrite = c+1;
                }
                else if (*c == '\r')
                {
                    stream.write(lastWrite, c-lastWrite);
                    stream << "\\r";
                    lastWrite = c+1;
                }
            }
            
            stream.write(lastWrite, c-lastWrite);
        }
    }
    else
        stream << text;
}

// *************************************************************************************************

} // namespace Devon
