// Devon
#include "pch.h"
#include <Devon/TestEnvironment.h>

namespace Devon {

// ************************************************************************************************
// BaseTestEnvironment class

class BaseTestEnvironment : public Devon::TestEnvironment
{    
public:
    BaseTestEnvironment() {}
    virtual ~BaseTestEnvironment() {}
    
    // Devon::TestEnvironment
    virtual void SetUp() {}
    virtual void TearDown() {}
    virtual void ImportTests(const std::string& name) {}
};

// ************************************************************************************************

} // namespace Devon

// ************************************************************************************************
// Devon Exported Function 

Devon::TestEnvironment*
GetTestEnvironment()
{
    static Devon::BaseTestEnvironment env;
    return &env;
}
