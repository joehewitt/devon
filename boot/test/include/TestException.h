#ifndef DEVON_TESTEXCEPTION_H
#define DEVON_TESTEXCEPTION_H

namespace Devon {

// *************************************************************************************************

class TestException
{
public:
    TestException(const std::string& title, const std::string& expectedValue,
       const std::string& actualValue, const std::string& message,
       const char* fileName="", int line=0)
        :   mMessage(message),
            mFileName(fileName),
            mLine(line),
            mTitle(title),
            mExpectedValue(expectedValue),
            mActualValue(actualValue)
    {
    }

    TestException(const TestException& other)
        :   mMessage(other.mMessage),
            mFileName(other.mFileName),
            mLine(other.mLine),
            mTitle(other.mTitle),
            mExpectedValue(other.mExpectedValue),
            mActualValue(other.mActualValue)
    {
    }

    virtual ~TestException() throw() {}

    inline const std::string& GetMessage() const { return mMessage; }

    inline const std::string& GetFileName() const { return mFileName; }

    inline unsigned int GetLine() const { return mLine; }

    inline std::string GetTitle() const { return mTitle; }

    inline std::string GetExpectedValue() const { return mExpectedValue; }

    inline std::string GetActualValue() const { return mActualValue; }

private:
    std::string mMessage;
    std::string mFileName;
    unsigned int mLine;

    std::string mTitle;
    std::string mExpectedValue;
    std::string mActualValue;
};

// *************************************************************************************************

class SetUpException
{
public:
    SetUpException() {}
    ~SetUpException() {}
};

// *************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTEXCEPTION_H
