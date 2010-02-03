#ifndef DEVON_MUTEX_H
#define DEVON_MUTEX_H

#include <pthread.h>

namespace Devon {

class DevonMutex
{
public:
    DevonMutex();
    ~DevonMutex();

    // For intrafunction locking and unlocking, use AutoMutex.  
    void Lock();
    void Unlock();    

private:

    pthread_mutex_t mMutex;
};

/**
 * Use this class to automatically release mutex ownership when the stack unwinds.
 * As a general rule, you should release ownership as soon as you no longer
 * need it, by calling Release().
 */
class AutoDevonMutex
{
public:
    AutoDevonMutex(DevonMutex* mutex)
        :   mMutex(mutex)
    {
        mMutex->Lock();
    }
    
    AutoDevonMutex(DevonMutex& mutex)
        :   mMutex(&mutex)
    {
        mMutex->Lock();
    }
    
    ~AutoDevonMutex()
    {
        Release();
    }

    void Release()
    {
        if (mMutex)
        {
            mMutex->Unlock();
            mMutex = NULL;
        }
    }
    
    void Unlock()
    {
        mMutex = NULL;
    }

private:
    DevonMutex* mMutex;
};

// *************************************************************************************************

} // namespace Devon

#endif // DEVON_MUTEX_H
