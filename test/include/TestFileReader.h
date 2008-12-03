#ifndef DEVON_TESTFILEREADER_H
#define DEVON_TESTFILEREADER_H

// Devon
#include <Devon/TestCase.h>

// STL
#include <string>
#include <vector>
#include <fstream>

namespace Devon {

// ************************************************************************************************

class TestReader
{
public:
    virtual ~TestReader() {}

    // TestReader
    virtual bool IsValid() = 0;
    virtual bool Next() = 0;
    virtual void Read(SectionList& sections) = 0;
};

// ************************************************************************************************

class TestFileReader : public TestReader
{
public:
    TestFileReader(const std::string& fileName);    
    virtual ~TestFileReader();

    static std::string ParseName(const std::string& fileName);

    // TestReader
    virtual bool IsValid();
    virtual bool Next();
    virtual void Read(SectionList& sections);

protected:
    bool ReadSection(SectionList& sections);

protected:
    std::string mFileName;
    unsigned int mLineNo;
    std::ifstream mStream;
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTFILEREADER_H

