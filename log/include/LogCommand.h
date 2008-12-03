#ifndef DEVON_LOGCOMMAND_H
#define DEVON_LOGCOMMAND_H

// STL
#include <string>

namespace Devon {

// ************************************************************************************************

class LogCommand
{
public:
    LogCommand(const std::string& name)
        :   mName(name)
    {
    }

    const std::string& GetName() const { return mName; }
    
protected:
    std::string mName;
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_LOGCOMMAND_H
