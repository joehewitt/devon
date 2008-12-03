#ifndef DEVON_STRINGLOG_H
#define DEVON_STRINGLOG_H

// Devon
#include <Devon/Log.h>

// STL
#include <sstream>

namespace Devon {

// ************************************************************************************************

class StringLog : public Log
{
public:
    StringLog()
        :   Log(mStringStream)
    {
    }
    
    StringLog(std::string& string)
        :   Log(mStringStream),
            mStringStream(string)
    {
    }
    
    std::stringstream& GetStream() { return mStringStream; }
    
    std::string GetString() const { return mStringStream.str(); }

    std::string ReleaseString()
    {
        std::string result = mStringStream.str();
        mStringStream.seekp(std::ios_base::beg);
        return result;
    }

protected:
    std::stringstream mStringStream;
};

// ************************************************************************************************

Log& NewStringLog();

std::string ReleaseStringLog(StringLog& log);

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_STRINGLOG_H
