#ifndef DEVON_TESTING_H
#define DEVON_TESTING_H

#include <Devon/logging.h>
#include <Devon/TestEnvironment.h>
#include <Devon/TestRunner.h>
#include <Devon/TestException.h>
#include <Devon/TestCase.h>
#include <Devon/TestSuite.h>
#include <Devon/TestFixture.h>
#include <Devon/TestFunction.h>
#include <Devon/TestFileFunction.h>
#include <Devon/asserts.h>

namespace Devon {

// *************************************************************************************************
// Test Fixture Creation

/**
 * TestFixtureDeclare is a convenience for declaring, instantiating, and registering a TestFixture
 * all in one swoop with a global variable.
 */
template <typename T>
class TestFixtureDeclare
{
public:
    TestFixtureDeclare()
    {
        T* fixture = new T();
        fixture->CreateTests();

        TestSuite* root = GetTestRoot();
        root->AddTest(fixture);
    }
};

// *************************************************************************************************

#define DEFINE_FIXTURE(__NAME) \
    __NAME() : ::Devon::TestFixture() {} \
    virtual ~__NAME() {} \
    virtual void CreateTests();

#define DEFINE_FIXTURE_AS(__NAME, __BASE) \
    __NAME() : __BASE() {} \
    virtual ~__NAME() {} \
    virtual void CreateTests();

#define DECLARE_BASE_FIXTURE(__NAME) \
	void \
    __NAME::CreateTests() \
	{ \
		typedef __NAME _tfixture; \
        \
        mName = #__NAME;

#define DECLARE_FIXTURE(__NAME) \
    static Devon::TestFixtureDeclare<__NAME> __NAME##_branch; \
    \
    extern ::Devon::TestFixture* __NAME##_create() { \
        return new __NAME(); \
    } \
    \
    DECLARE_BASE_FIXTURE(__NAME)

#define DECLARE_FIXTURE_AS(__NAME, __BASE) \
    static Devon::TestFixtureDeclare<__NAME> __NAME##_branch; \
    \
    extern ::Devon::TestFixture* __NAME##_create() { \
        return new __NAME(); \
    } \
    \
	void \
    __NAME::CreateTests() \
	{ \
		typedef __NAME _tfixture; \
        \
        __BASE::CreateTests(); \
        mName = #__NAME;

#define END_DECLARE_FIXTURE \
	}

#define DECLARE_DUMPER(__NAME) \
    void __NAME(const std::string& source, const Devon::Section& section, \
        std::ostream& stream);

#define DECLARE_TEST(__NAME) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFunction<_tfixture>(#__NAME, \
                *this, &_tfixture::__NAME); \
            mTests.push_back(test); \
        }

#define DECLARE_TEST_FILE(__FILENAME) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFileFunction<_tfixture>( \
                new ::Devon::TestFileReader(__FILENAME), \
                ::Devon::TestFileReader::ParseName(__FILENAME), \
                *this); \
            mTests.push_back(test); \
        }

#define DECLARE_TEST_FILE_DEFAULT(__FILENAME, __DEFAULT) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFileFunction<_tfixture>( \
                new ::Devon::TestFileReader(__FILENAME), \
                ::Devon::TestFileReader::ParseName(__FILENAME), \
                *this, \
                __DEFAULT); \
            mTests.push_back(test); \
        }

#define DECLARE_TEST_FILE_FUNCTION(__FILENAME, __FUNCTION) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFileFunction<_tfixture>( \
                new ::Devon::TestFileReader(__FILENAME), \
                ::Devon::TestFileReader::ParseName(__FILENAME), \
                *this, \
                static_cast< ::Devon::TestFixture::CompareFunction >(&_tfixture::__FUNCTION)); \
            mTests.push_back(test); \
        }

#define SKIP_TEST_FILE_FUNCTION(__FILENAME, __FUNCTION) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFileFunction<_tfixture>( \
                new ::Devon::TestFileReader(__FILENAME), \
                ::Devon::TestFileReader::ParseName(__FILENAME), \
                *this, \
                static_cast< ::Devon::TestFixture::CompareFunction >(&_tfixture::__FUNCTION), \
                ::Devon::FunctionType, ::Devon::SkipStatus); \
            mTests.push_back(test); \
        }

#define DECLARE_INSPECTOR(__NAME) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFunction<_tfixture>(#__NAME, \
                *this, &_tfixture::__NAME, ::Devon::InspectorType); \
            mTests.push_back(test); \
        }

#define DECLARE_INSPECTOR_FILE(__FILENAME) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFileFunction<_tfixture>( \
                new ::Devon::TestFileReader(__FILENAME), \
                ::Devon::TestFileReader::ParseName(__FILENAME), \
                *this, \
                "", \
                ::Devon::InspectorType); \
            mTests.push_back(test); \
        }

#define DECLARE_INSPECTOR_FILE_DEFAULT(__FILENAME, __DEFAULT) \
        { \
            ::Devon::TestCase* test = new ::Devon::TestFileFunction<_tfixture>( \
                new ::Devon::TestFileReader(__FILENAME), \
                ::Devon::TestFileReader::ParseName(__FILENAME), \
                *this, \
                __DEFAULT, \
                ::Devon::InspectorType); \
            mTests.push_back(test); \
        }

#define DECLARE_TEST_DUMPER(__NAME, __KEY) \
        AddDumper(__KEY, static_cast< ::Devon::TestFixture::DumpFunction >(&_tfixture::__NAME));

// *************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTING_H
