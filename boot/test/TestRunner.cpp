// Devon
#include "pch.h"
#include <Devon/TestRunner.h>
#include <Devon/TestEnvironment.h>
#include <Devon/TestException.h>
#include <Devon/TestCase.h>
#include <Devon/TestSuite.h>

// DevonLog
#include <Devon/logging.h>

// STL
#include <fstream>

namespace Devon {

// *************************************************************************************************
// Constants

#ifdef WIN32
static const char* kTestCatalogInputPath = "c:/temp/DevonTestCatalogInput.txt";
static const char* kTestCatalogOutputPath = "c:/temp/DevonTestCatalogOutput.txt";
#else
static const char* kTestCatalogInputPath = "/tmp/DevonTestCatalogInput.txt";
static const char* kTestCatalogOutputPath = "/tmp/DevonTestCatalogOutput.txt";
#endif

// *************************************************************************************************
// Local Helpers

static void
LogTestsCatalog(TestCase* testCase)
{
    static std::ofstream logStream(kTestCatalogOutputPath, std::ios::app);
    static Log log(logStream, "Catalog Output Log");
    
    std::string name = testCase->name();
    std::string status = testCase->status() == SkipStatus ? "skip" : "";
    TestType type = testCase->type();
    log << LOG_COMMAND("declareTest", ATTR(name, name) << ATTR(testType, (int)type)
        << ATTR(testStatus, status));
    
    unsigned int count = testCase->testCount();
    for (unsigned int i = 0; i < count; ++i)
    {
        TestCase* test = testCase->GetTest(i);
        LogTestsCatalog(test);
    }

    log << LOG_COMMAND("endDeclareTest", "");
}

static void
LogLogsCatalog(Log* log)
{
    unsigned int count = log->GetCategoryCount();
    for (unsigned int i = 0; i < count; ++i)
    {
        LogCategory* category = log->GetCategory(i);

        LOGEX(LOG_COMMAND("declareCategory",
            ATTR(name, category->GetName()) << ATTR(disabled, category->GetDisabled())));
    }
}

static void
ReadTextFile(const char* path, std::string& lines)
{
    char buffer[1024];
    
    // XXXjoe Use C++ STL iostreams
    FILE* catalogFile = fopen(path, "r");
    if (!catalogFile)
        return;

    int count = 0;
    do
    {
        count = fread(buffer, 1, 1023, catalogFile);
        if (count > 0)
        {
            buffer[count] = 0;
            lines.append(buffer);
        }
    } while (count > 0);
    fclose(catalogFile);
}

static void
ImportExtraTests(TestEnvironment* env)
{
    std::string lines;
    ReadTextFile(kTestCatalogInputPath, lines);

    env->SetUp();
    
    // Read each line of the extras file and create a test for the name on each line
    unsigned int begin = 0;
    unsigned int offset = lines.find('\n');
    while (offset != -1)
    {
        const std::string& line = lines.substr(begin, offset-begin);
        env->ImportTests(line);
        
        begin = offset+1;
        offset = lines.find('\n', begin);
    }
    
    env->TearDown();
}

static bool
SetUpTest(TestCase* test)
{
    LOGEX(LOG_COMMAND("beginTest", ATTR(name, test->name())));

    try {
        test->SetUp();
        return true;
    }
    catch (const SetUpException& exc)
    {
        return false;
    }
    catch (const std::exception& exc)
    {
        LOGEX(LOG_COMMAND("testExceptionThrown", ATTR(message, exc.what())));
        return false;
    }
#ifndef WIN32
    catch (...)
    {
        LOGEX(LOG_COMMAND("testExceptionThrown", ""));
        return false;
    }
#endif
}

static bool
TearDownTest(TestCase* test)
{
    try {
        test->TearDown();
        LOGEX(LOG_COMMAND("endTest", ""));
        return true;
    }
    catch (const std::exception& exc)
    {
        LOGEX(LOG_COMMAND("testExceptionThrown", ATTR(message, exc.what())));
    }
#ifndef WIN32
    catch (...)
    {
        LOGEX(LOG_COMMAND("testExceptionThrown", ""));
    }
#endif

    LOGEX(LOG_COMMAND("endTest", ""));
    return false;
}

static bool
RunTest(TestCase* test)
{
    if (test->status() == SkipStatus)
        return true;

    try {
        test->Run();
        return true;
    }
    catch (const TestException& exc)
    {
        LOGEX(LOG_COMMAND("assertionFailed", 
            ATTR(title, exc.GetTitle())
            << ATTR(var0, "Expression")
            << ATTR(val0, exc.GetMessage())
            << ATTR(var1, "Actual")
            << ATTR(val1, exc.GetActualValue())
            << ATTR(var2, "Expected")
            << ATTR(val2, exc.GetExpectedValue())
            << ATTR(fileName, exc.GetFileName())
            << ATTR(line, exc.GetLine())));
        return false;
    }
    catch (const std::exception& exc)
    {
        LOGEX(LOG_COMMAND("testExceptionThrown", ATTR(message, exc.what())));
        return false;
    }
#ifndef WIN32
    catch (...)
    {
        LOGEX(LOG_COMMAND("testExceptionThrown", ""));
        return false;
    }
#endif
}

static bool
RunTestBranch(TestCase* test, const std::string& testName="", bool runAll=true)
{
    if (test->status() == SkipStatus)
        return true;

    bool passed = true;
    if (SetUpTest(test))
    {
        bool isGroup = test->type() == FixtureType || test->type() == SuiteType;
        unsigned int count = test->testCount();

        if (runAll)
        {
            if (!isGroup)
                passed = RunTest(test);

            for (unsigned int i = 0; i < count; ++i)
            {
                TestCase* subTest = test->GetTest(i);
                if (subTest->type() != InspectorType && !RunTestBranch(subTest, "", true))
                    passed = false;
            }
        }
        else
        {
            size_t slash = testName.find('/');
            std::string subName = slash == std::string::npos ? testName : testName.substr(0, slash);
            std::string remainingName = slash == std::string::npos ? "" : testName.substr(slash+1);
                
            for (unsigned int i = 0; i < count; ++i)
            {
                TestCase* subTest = test->GetTest(i);
                if (subTest->name() == subName)
                {
                    if (slash == std::string::npos)
                        passed = RunTestBranch(subTest);
                    else
                        passed = RunTestBranch(subTest, remainingName, false);
                    break;
                }
            }
        }
    }
    else
        passed = false;
    
    // XXXblake Tearing down the test even if it failed is necessary, but might lead to
    // additional exceptions/warnings if the teardown tries to clean up something that never got
    // created due to premature exit from setup.
    // XXXblake If we turned test constructors and destructors into setup/teardown functions (and
    // just created a new instance each time the test is run), we can rely more on member objects
    // and not have to worry about initializing pointers to NULL so teardown deletes don't crash (and
    // then re-initializing them to NULL in teardown).
    // XXXjoe We're not currently reporting when an exception happens in TearDown
    TearDownTest(test);
    
    return passed;
}

// *************************************************************************************************

TestSuite*
GetTestRoot()
{
    static TestSuite root("Tests");
    return &root;
}

void
Run(TestEnvironment* env, const std::string& mode, const std::string& target)
{
    ImportExtraTests(env);

    TestSuite* testRoot = GetTestRoot();
    if (!testRoot)
        return;
        
    if (mode == "testCatalog")
        LogTestsCatalog(testRoot);
    else if (mode == "logCatalog")
    {
        Log& logRoot = Log::GetRootLog();
        LogLogsCatalog(&logRoot);
    }
    else
    {
        if (target.empty())
            RunTestBranch(testRoot);
        else
        {
            size_t slash = target.find('/');
            if (slash == std::string::npos)
            {
                if (testRoot->name() == target)
                    RunTestBranch(testRoot);
            }
            else
                RunTestBranch(testRoot, target.substr(slash+1), false);
        }
    }
}

// *************************************************************************************************

} // namespace Devon
