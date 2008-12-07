#ifndef DEVON_GLOBAL_ASSERTS_H
#define DEVON_GLOBAL_ASSERTS_H

//**************************************************************************************************
// Assertions

#define DV_ASSERT(__condition) \
    if (!(__condition)) \
    { \
        throw ::Devon::TestException("Assert", \
            "", \
            "", \
            #__condition, \
            __FILE__, __LINE__); \
    } 

#define DV_ASSERT_EQUAL_SECTION(__lhs, __rhs, __section) \
    if (!((__lhs) == (__rhs))) \
    { \
        throw ::Devon::TestException("Equality Assert", \
            LOG_STRING(__rhs), \
            LOG_STRING(__lhs), \
            #__lhs " == " #__rhs, \
            __section.find("__file__")->second.c_str(), \
            strtol(__section.find("__line__")->second.c_str(), NULL, 10)); \
    } 

#define DV_ASSERT_EQUAL(__lhs, __rhs) \
    if (!((__lhs) == (__rhs))) \
    { \
        throw ::Devon::TestException("Equality Assert", \
            LOG_STRING(__rhs), \
            LOG_STRING(__lhs), \
            #__lhs " == " #__rhs, \
            __FILE__, __LINE__); \
    } 

#define DV_ASSERT_NEQUAL(__lhs, __rhs) \
    if ((__lhs) == (__rhs)) \
    { \
        throw ::Devon::TestException("Not Equal Assert", \
            LOG_STRING(__rhs), \
            LOG_STRING(__lhs), \
            #__lhs " != " #__rhs, \
            __FILE__, __LINE__); \
    } 

#define DV_ASSERT_GTE(__lhs, __rhs) \
    if ((__lhs) < (__rhs)) \
    { \
        throw ::Devon::TestException("Greater Than or Equal Assert", \
            LOG_STRING(__rhs), \
            LOG_STRING(__lhs), \
            #__lhs " >= " #__rhs, \
            __FILE__, __LINE__); \
    } 

#define DV_ASSERT_GT(__lhs, __rhs) \
    if ((__lhs) <= (__rhs)) \
    { \
        throw ::Devon::TestException("Greater Than Assert", \
            LOG_STRING(__rhs), \
            LOG_STRING(__lhs), \
            #__lhs " > " #__rhs, \
            __FILE__, __LINE__); \
    } 

#define DV_FAIL() \
    throw ::Devon::TestException("failure", "", "", "failure", __FILE__, __LINE__);

//**************************************************************************************************

#endif // DEVON_GLOBAL_ASSERTS_H
