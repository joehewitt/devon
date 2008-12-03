// Devon
#include "pch.h"
#include "Devon/TestSuite.h"

// STL
#include <algorithm>

namespace Devon {

//**************************************************************************************************
// TestSuite class public

TestSuite::TestSuite(const std::string& name)
    :   m_name(name)
{
}

TestSuite::~TestSuite()
{
    TestCaseArray::iterator iter = m_tests.begin();
    TestCaseArray::iterator iterEnd = m_tests.end();
    for (iter; iter != iterEnd; ++iter)
        delete *iter;
}

void
TestSuite::AddTest(TestCase* testCase)
{
    m_tests.push_back(testCase);
}

void
TestSuite::RemoveTest(TestCase* testCase)
{
    m_tests.erase(std::remove(m_tests.begin(), m_tests.end(), testCase));
}

//**************************************************************************************************
// TestSuite : TestCase class public

const std::string&
TestSuite::name() const
{
    return m_name;
}

TestType
TestSuite::type() const
{
    return Devon::SuiteType;
}

unsigned int
TestSuite::testCount() const
{
    return m_tests.size();
}

TestCase*
TestSuite::GetTest(unsigned int index) const
{    
    return m_tests[index];
}

void
TestSuite::SetUp()
{
}

void
TestSuite::TearDown()
{
}

void
TestSuite::Run()
{
}

// *************************************************************************************************

} // namespace Devon
