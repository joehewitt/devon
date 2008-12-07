// Devon
#include "pch.h"
#include "Devon/TestFixture.h"

// stdlib
#include <stdarg.h>

namespace Devon {

//**************************************************************************************************
// TestFixture class public

TestFixture::TestFixture()
{
}

TestFixture::~TestFixture()
{
    TestCaseArray::iterator iter = mTests.begin();
    TestCaseArray::iterator iterEnd = mTests.end();
    for (iter; iter != iterEnd; ++iter)
        delete *iter;
}

void
TestFixture::SetUpTest()
{
}

void
TestFixture::TearDownTest()
{
}

void
TestFixture::HandleKey(const std::string& key, const Section& section)
{
}

TestFixture::DumpFunction
TestFixture::FindDumpFunction(const std::string& name)
{                         
    DumperMap::const_iterator iter = mDumpers.find(name);
    if (iter == mDumpers.end())
        return NULL;
    else
        return iter->second;
}

void
TestFixture::AddDumper(const std::string& name, DumpFunction dumper)
{
    mDumpers[name] = dumper;
}

//**************************************************************************************************
// TestFixture : TestCase class public

const std::string&
TestFixture::name() const
{
    return mName;
}

TestType
TestFixture::type() const
{
    return Devon::FixtureType;
}

unsigned int
TestFixture::testCount() const
{
    return mTests.size();
}

TestCase*
TestFixture::GetTest(unsigned int index) const
{
    return mTests[index];
}

void
TestFixture::SetUp()
{
}

void
TestFixture::TearDown()
{
}

void
TestFixture::Run()
{
}

//**************************************************************************************************

} // namespace Devon
