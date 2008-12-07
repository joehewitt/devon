#ifndef DEVON_TESTSUITE_H
#define DEVON_TESTSUITE_H

// Devon
#include <Devon/TestCase.h>

// STL
#include <string>
#include <vector>

namespace Devon {

class TestCase;

// ************************************************************************************************

class TestSuite : public TestCase
{
public:
	TestSuite(const std::string& name);
    virtual ~TestSuite();
    
    void AddTest(TestCase* testCase);
    void RemoveTest(TestCase* testCase);

	///////////////////////////////////////////////////////////////////////////////////////////////
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

protected:
    std::string m_name;
    TestCaseArray m_tests;
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTSUITE_H
