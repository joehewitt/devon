
// Devon
#include <Devon/StringLog.h>

namespace Devon {

// *************************************************************************************************
// Global Functions

Log& NewStringLog()
{
    StringLog* log = new StringLog();
    return *log;
}

std::string ReleaseStringLog(StringLog& log)
{
    std::string result = log.GetString();
    delete &log;
    return result;
}

// *************************************************************************************************

} // namespace Devon
