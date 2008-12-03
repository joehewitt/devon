// Devon
#include "pch.h"
#include <Devon/TestFileReader.h>

namespace Devon {

// *************************************************************************************************
// Local Helpers

template <typename TLeft>
std::string
ToString(const TLeft& value)
{
	std::ostringstream msgOut;
	msgOut << value;
	return msgOut.str();
}
                                  
static void
TrimWhitespace(std::string& s1)
{
    const char* whiteChars = "\n\t \r";
    
    size_t notWhite = s1.find_first_not_of(whiteChars);
    s1.erase(0, notWhite);

    notWhite = s1.find_last_not_of(whiteChars);
    s1.erase(notWhite+1);
}

// *************************************************************************************************

TestFileReader::TestFileReader(const std::string& fileName)
    :   mFileName(fileName),
        mLineNo(0),
        mStream(fileName.c_str(), std::fstream::binary)
{
    // XXXblake If we open the stream above in (default) text mode, files with Unix line endings are
    // not read properly on Windows... tellg() messes up the get position.

    // XXXblake Need to do this for all devon ifstreams or use FileStream
    mStream.exceptions(std::fstream::badbit | std::fstream::failbit);
}

TestFileReader::~TestFileReader()
{
}

std::string
TestFileReader::ParseName(const std::string& fileName)
{
    int indexSlash = fileName.rfind('/');
    if (indexSlash == -1)
        return fileName;
    
    int indexDot = fileName.rfind('.');
    if (indexDot == -1)
        return fileName.substr(indexSlash+1);

    return fileName.substr(indexSlash+1, (indexDot-indexSlash)-1);
}

bool
TestFileReader::IsValid()
{
    std::ifstream& stream = const_cast<std::ifstream&>(mStream);
    // XXXjoe I know, you're thinking, why not just use stream.eof() ? We were,
    // but it wasn't working! At least not on Mac OS X.  I was getting
    // failure exceptions from getline when trying to read an empty line
    // at the end of the file
    int was = stream.tellg();
    stream.seekg(0, std::ios::end);
    int len = stream.tellg();
    stream.seekg(was);
    return was != len;
}

bool
TestFileReader::Next()
{
    return true;
}

void
TestFileReader::Read(SectionList& sections)
{
    while (ReadSection(sections))
        1;
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
// TestFileReader class protected

bool
TestFileReader::ReadSection(SectionList& sections)
{
    unsigned int sectionLineNo = 0;
    char line[0x0000ffff];
    bool pastHeader = false;
    bool lastSection = false;
    std::string body;
    
    std::string sectionDelim = "~~~~~~~~~~";
    std::string blockDelim = "==========";
    
    Section section;
    
    while (mStream.getline(line, 0x0000ffff))
    {
        ++mLineNo;
        
        if (strstr(line, blockDelim.c_str()) == line)
        {
            lastSection = true;
            break;
        }
        else if (strstr(line, sectionDelim.c_str()) == line)
            break;
        else if (pastHeader || (line[0] != '#' && line[0] != '%'))
        {
            pastHeader = true;
            if (!sectionLineNo)
                sectionLineNo = mLineNo;
            
            body += line;
            body += "\n";
        }
        else if (line[0] == '%')
        {
            std::string value = line+1;
            TrimWhitespace(value);
            
            int colon = value.find(":");
            if (colon != -1)
            {
                std::string key = value.substr(0, colon);
                std::string keyValue = value.substr(colon+1);

                TrimWhitespace(key);
                TrimWhitespace(keyValue);
                
                section[key] = keyValue;
            }
            else
                section[value] = "";
        }
    }
    
    TrimWhitespace(body);
    if (!body.empty())
    {
        section["body"] = body;
        section["__file__"] = mFileName;
        section["__line__"] = ToString(sectionLineNo);
        sections.push_back(section);
    }
    
    return !lastSection && IsValid();
}

// *************************************************************************************************

} // namespace Devon
