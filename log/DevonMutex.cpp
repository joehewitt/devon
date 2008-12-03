// Devon
#include <Devon/logging.h>
#include "DevonMutex.h"

// stdlib
#include <errno.h>

namespace Devon {

// ************************************************************************************************
// DevonMutex class public

DevonMutex::DevonMutex()
{
    pthread_mutexattr_t mutexTypeAttr;
    int rv = ::pthread_mutexattr_init(&mutexTypeAttr);
    WARN_IF(rv, "Error initializing mutex attributes");

    rv = ::pthread_mutexattr_settype(&mutexTypeAttr, PTHREAD_MUTEX_ERRORCHECK);
    WARN_IF(rv, "Error setting mutex attributes");

    rv = ::pthread_mutex_init(&mMutex, &mutexTypeAttr);
    WARN_IF(rv, "Error initializing mutex");
}

DevonMutex::~DevonMutex()
{
    int rv = ::pthread_mutex_destroy(&mMutex);
    WARN_IF(rv, "Error destroying mutex");
}

void
DevonMutex::Lock()
{
    //NOTE_CREATE("Lock mutex " << this);

    int rv = ::pthread_mutex_lock(&mMutex);
    WARN_IF(rv, "Error " << rv << " acquiring mutex lock");
}

void
DevonMutex::Unlock()
{
    //NOTE_DESTROY("Unlock mutex " << this);

    int rv = ::pthread_mutex_unlock(&mMutex);
    WARN_IF(rv, "Error " << rv << " releasing mutex lock");
}

// ************************************************************************************************

} // namespace Devon
