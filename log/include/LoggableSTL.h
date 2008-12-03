#ifndef DEVON_LOGGABLESTL_H
#define DEVON_LOGGABLESTL_H

// STL
#include <vector>
#include <map>

namespace Devon {

class Log;

// ************************************************************************************************

template <typename TItem>
class Loggable<std::vector<TItem> >
{
public:
    typedef const std::vector<TItem> VectorType;
    
    static void Write(Log& log, VectorType& vector)
    {
        typename VectorType::const_iterator iter = vector.begin();
        typename VectorType::const_iterator iterEnd = vector.end();
        for (iter; iter != iterEnd; ++iter)
            log << *iter << ", ";
    }
};

// ************************************************************************************************

template <typename TKey, typename TItem>
class Loggable<std::map<TKey, TItem> >
{
public:
    typedef const std::map<TKey, TItem> MapType;
    
    static void Write(Log& log, MapType& map)
    {
        typename MapType::const_iterator iter = map.begin();
        typename MapType::const_iterator iterEnd = map.end();
        for (iter; iter != iterEnd; ++iter)
            log << iter->first << ":" << iter->second << ", ";
    }
};

// ************************************************************************************************

} // namespace Devon

#endif // DEVON_LOGGABLESTL_H
