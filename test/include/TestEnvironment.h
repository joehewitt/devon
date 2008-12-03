#ifndef DEVON_TESTENVIRONMENT_H
#define DEVON_TESTENVIRONMENT_H

// std
#include <string>

namespace Devon {

// ************************************************************************************************

class TestEnvironment
{
public:
    virtual ~TestEnvironment() {}
    
    virtual void SetUp() = 0;
    
    virtual void TearDown() = 0;

    virtual void ImportTests(const std::string& name) = 0;
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTENVIRONMENT_H

