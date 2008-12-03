#ifndef DEVON_TESTFIXTURE_H
#define DEVON_TESTFIXTURE_H

// Devon
#include <Devon/TestCase.h>

// STL
#include <vector>
#include <iostream>

namespace Devon {

// ************************************************************************************************

class TestFixture : public TestCase
{
public:    
    typedef void (TestFixture::*DumpFunction)(const std::string& source, const Section& section,
        std::ostream& stream);
    typedef void (TestFixture::*CompareFunction)(const std::string& source,
        const std::string& expected);

public:
    TestFixture();
    virtual ~TestFixture();
        
    virtual void CreateTests() = 0;
    virtual void SetUpTest();
    virtual void TearDownTest();                                        
    virtual void HandleKey(const std::string& key, const Section& section);
   
    void AddDumper(const std::string& name, DumpFunction dumper);
    DumpFunction FindDumpFunction(const std::string& name);

public:
    // TestCase
    virtual const std::string& name() const;
    virtual TestType type() const;
    virtual TestStatus status() const { return RunStatus; }
    virtual unsigned int testCount() const; 
    virtual TestCase* GetTest(unsigned int index) const; 
    virtual void SetUp();
    virtual void TearDown();
    virtual void Run();
    
protected:
    typedef std::vector<TestCase*> TestCaseArray;
    typedef std::map<std::string, DumpFunction> DumperMap;

protected:
    std::string mName;
    TestCaseArray mTests;
    DumperMap mDumpers;
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTFIXTURE_H

