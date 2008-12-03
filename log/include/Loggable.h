#ifndef DEVON_LOGGABLE_H
#define DEVON_LOGGABLE_H

namespace Devon {

class Log;

// ************************************************************************************************

template <typename T>
class Loggable
{
public:    
    static void Write(Log& log, const T& object);
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_LOGGABLE_H
