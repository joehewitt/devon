#ifndef DEVON_LOGEVENT_H
#define DEVON_LOGEVENT_H

namespace Devon {

// ************************************************************************************************

class LogEvent
{
public:
    LogEvent(const std::string& name)
        :   mName(name)
    {
    }

    const std::string& GetName() const { return mName; }

protected:
    std::string mName;
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_LOGEVENT_H
