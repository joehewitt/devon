#ifndef DEVON_TESTFUNCTION_H
#define DEVON_TESTFUNCTION_H

// Devon
#include <Devon/TestCase.h>

namespace Devon {

// ************************************************************************************************

template <typename TFixture>
class TestFunction : public TestCase
{
public:
    typedef void (TFixture::*TestFn)();

public:
    TestFunction(const std::string& name, TFixture& fixture, TestFn fn=NULL,
        TestType type=FunctionType, TestStatus status=RunStatus);
    virtual ~TestFunction();

    // TestCase    
    virtual const std::string& name() const;
    virtual TestType type() const;
    virtual TestStatus status() const { return mStatus; }
    virtual unsigned int testCount() const;
    virtual TestCase* GetTest(unsigned int index) const;
    virtual void SetUp();
    virtual void TearDown();
    virtual void Run();

protected:
    std::string mName;
    TestType mType;
    TestStatus mStatus;
    TFixture& mFixture; // weak
    TestFn mFunction;
};

//**************************************************************************************************
// TestFunction class public

template <typename TFixture>
TestFunction<TFixture>::TestFunction(const std::string& name, TFixture& fixture, TestFn fn,
    TestType type, TestStatus status)
    :   mName(name),
        mType(type),
        mFixture(fixture),
        mFunction(fn),
        mStatus(status)
{
}

template <typename TFixture>
TestFunction<TFixture>::~TestFunction()
{
}

//**************************************************************************************************
// TestFunction : TestCase class public

template <typename TFixture>
const std::string&
TestFunction<TFixture>::name() const
{
    return mName;
}

template <typename TFixture>
TestType
TestFunction<TFixture>::type() const
{
    return mType;
}

template <typename TFixture>
unsigned int
TestFunction<TFixture>::testCount() const
{
    return 0;
}

template <typename TFixture>
TestCase*
TestFunction<TFixture>::GetTest(unsigned int index) const
{
    //REQUIRE(false, Exception, NotImplementedError, "");
    return NULL;
}

template <typename TFixture>
void
TestFunction<TFixture>::SetUp()
{
}

template <typename TFixture>
void
TestFunction<TFixture>::TearDown()
{
}

template <typename TFixture>
void
TestFunction<TFixture>::Run()
{
    (mFixture.*mFunction)();
}

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTFUNCTION_H

