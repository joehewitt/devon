#ifndef DEVON_TESTFILEFUNCTION_H
#define DEVON_TESTFILEFUNCTION_H

// Devon
#include <Devon/TestFunction.h>
#include <Devon/TestFileReader.h>
#include <Devon/logging.h>
#include <Devon/asserts.h>

// STL
#include <iostream>

namespace Devon {

// *************************************************************************************************
// Local Helpers
                              
static void
TrimWhitespace(std::string& s1)
{
    const char* whiteChars = "\n\t \r";
    
    size_t notWhite = s1.find_first_not_of(whiteChars);
    s1.erase(0, notWhite);

    notWhite = s1.find_last_not_of(whiteChars);
    s1.erase(notWhite+1);
}

class AutoTearDownTest
{
public:
    AutoTearDownTest(TestFixture& fixture)
        :   mFixture(fixture)
    {
        mFixture.SetUpTest();
    }

    ~AutoTearDownTest()
    {
        mFixture.TearDownTest();
    }   

private:
    TestFixture& mFixture;
};

// ************************************************************************************************

template <typename TFixture>
class TestFileFunction : public TestFunction<TFixture>
{
public:
    TestFileFunction(TestReader* reader, const std::string& name, TFixture& fixture,
                     const std::string& defaultTestType="", TestType type=FunctionType,
                     TestStatus status=RunStatus);
    TestFileFunction(TestReader* reader, const std::string& name, TFixture& fixture,
                     TestFixture::CompareFunction function, TestType type=FunctionType,
                     TestStatus status=RunStatus);
    virtual ~TestFileFunction();

    void DoDump(const std::string& dumpType, const Section& section, TestFixture::DumpFunction function);
    void DoTest(const std::string& dumpType, const std::string& source, const Section& section,
        TestFixture::DumpFunction function);

    // TestCase
    virtual void Run();

protected:
    TestReader* mReader; // strong
    TestFixture::CompareFunction mTestFunction;
    std::string mDefaultTestType;
};

//**************************************************************************************************
// TestFileFunction class public

template <typename TFixture>
TestFileFunction<TFixture>::TestFileFunction(TestReader* reader,
        const std::string& name, TFixture& fixture,
        const std::string& defaultTestType, TestType type, TestStatus status)
    :   TestFunction<TFixture>(name, fixture, NULL, type, status),
        mReader(reader),
        mTestFunction(NULL),
        mDefaultTestType(defaultTestType)
{
}

template <typename TFixture>
TestFileFunction<TFixture>::TestFileFunction(TestReader* reader,
        const std::string& name, TFixture& fixture,
        TestFixture::CompareFunction function, TestType type, TestStatus status)
    :   TestFunction<TFixture>(name, fixture, NULL, type, status),
        mReader(reader),
        mTestFunction(function)
{
}

template <typename TFixture>
TestFileFunction<TFixture>::~TestFileFunction()
{
    delete mReader;
}

template <typename TFixture>  
void
TestFileFunction<TFixture>::DoDump(const std::string& dumpType, const Section& section,
    TestFixture::DumpFunction function)
{
    AUTOSTART("Dumping " << dumpType);

    const std::string& source = section.find("body")->second;
    std::stringstream stream;

    (this->mFixture.*function)(source, section, stream);

    std::string dump = stream.str();
    LOG_RAW(dump);
}

template <typename TFixture>  
void
TestFileFunction<TFixture>::DoTest(const std::string& dumpType, const std::string& source,
    const Section& section, TestFixture::DumpFunction function)
{
    const std::string& expected = section.find("body")->second;
    bool identical = section.find("identical") != section.end();

    std::stringstream stream;

    try
    {
        (this->mFixture.*function)(source, section, stream);
    }
    catch (const std::exception& exc)
    {
        std::string message = exc.what();
        TrimWhitespace(message);
        
        DV_ASSERT_EQUAL_SECTION(message, expected, section);
        return;
    }

    std::string actual = stream.str();
    TrimWhitespace(actual);
                                           
    if (identical)
    {
        DV_ASSERT_EQUAL_SECTION(actual, source, section);
    }
    else
    {
        DV_ASSERT_EQUAL_SECTION(actual, expected, section);
    }
}

//**************************************************************************************************
// TestFileFunction : TestCase class public

inline bool
IsSkipped(const Devon::Section& section)
{
    return section.find("skip") != section.end()
        || section.find("nyi") != section.end();
}

template <typename TFixture>
void
TestFileFunction<TFixture>::Run()
{
    for (mReader; mReader->IsValid(); mReader->Next())
    {
        SectionList sections;
        mReader->Read(sections);

        if (!sections.empty())
        {
            bool ranTest = false;
            
            const Devon::Section& sourceSection = sections.front();
            bool skipAll = IsSkipped(sourceSection);
            
            AutoTearDownTest autoTearDown(this->mFixture);
            
            SectionList::const_iterator iter = sections.begin(), iterEnd = sections.end();
            for (; iter != iterEnd; ++iter)
            {
                const Devon::Section& section = *iter;

                Devon::Section::const_iterator keyIter = section.begin(), keyIterEnd = section.end();
                for (; keyIter != keyIterEnd; ++keyIter)
                {
                    const std::string& key = keyIter->first;
                    this->mFixture.HandleKey(key, section); 
                }
            }
            
            iter = sections.begin(), iterEnd = sections.end();
            for (; iter != iterEnd; ++iter)
            {
                const Devon::Section& section = *iter;

                Devon::Section::const_iterator keyIter = section.begin(), keyIterEnd = section.end();
                for (; keyIter != keyIterEnd; ++keyIter)
                {
                    const std::string& key = keyIter->first;
                    if (key == "test")
                    {
                        if (skipAll || IsSkipped(section))
                            continue;
                        
                        ranTest = true;

                        const std::string& source = sourceSection.find("body")->second;

                        const std::string& testType = section.find("test")->second;
                        TestFixture::DumpFunction function = 
                            this->mFixture.FindDumpFunction(testType);
                        if (function)
                            DoTest(testType, source, section, function);
                    }   
                    else if (key == "dump")
                    {
                        const std::string& testType = section.find("dump")->second;
                        TestFixture::DumpFunction function = 
                            this->mFixture.FindDumpFunction(testType);
                        if (function)
                            DoDump(testType, section, function);
                    }   
                }
            }    
            
            if (!ranTest && !skipAll)
            if (mTestFunction)
            {
                const Devon::Section& sourceSection = sections.front();
                const std::string& source = sourceSection.find("body")->second;

                Devon::Section& lastSection = sections.back();
                const std::string& expected = lastSection.find("body")->second;

                (this->mFixture.*mTestFunction)(source, expected);
            }
            else if (!mDefaultTestType.empty())
            {                                     
                const Devon::Section& sourceSection = sections.front();
                const std::string& source = sourceSection.find("body")->second;

                Devon::Section& lastSection = sections.back();
                TestFixture::DumpFunction function = 
                    this->mFixture.FindDumpFunction(mDefaultTestType);
                if (function)
                    DoTest(mDefaultTestType, source, lastSection, function);
            }
        }
    }
}

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTFILEFUNCTION_H

