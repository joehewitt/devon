#ifndef DEVON_TESTRUNNER_H
#define DEVON_TESTRUNNER_H

// STL
#include <string>

namespace Devon {

class TestSuite;
class TestEnvironment;

// ************************************************************************************************

TestSuite* GetTestRoot();

void Run(TestEnvironment* env, const std::string& mode="", const std::string& target="");

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_TESTRUNNER_H
