#ifndef DEVON_TESTCASE_H
#define DEVON_TESTCASE_H

// std
#include <string>

namespace Devon {

// ************************************************************************************************

enum TestType {
    UnknownType,
    FixtureType,
    SuiteType,
    WrapperType,
    FunctionType,
    InspectorType
};

enum TestStatus
{
    RunStatus,
    SkipStatus,
};

class TestCase
{
public:
    virtual ~TestCase() {}
    
    virtual const std::string& name() const = 0; 
    
    virtual TestStatus status() const = 0;

    virtual TestType type() const = 0;

    virtual unsigned int testCount() const = 0;

    virtual TestCase* GetTest(unsigned int index) const = 0;

    virtual void SetUp() = 0;
    
    virtual void TearDown() = 0;

    virtual void Run() = 0;
};

// ************************************************************************************************

typedef std::map<std::string, std::string> Section;
typedef std::vector<Section> SectionList;

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTCASE_H

