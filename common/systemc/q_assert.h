#ifndef ASSERT_H
#define ASSERT_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <string>
#include <sstream>
#include <iostream>
#include <cassert>


void q_assert_body(bool dump, const char * file, int line, std::string ctx, std::string msg, std::string ctx_msg);

//#define RUNNING_IN_DEBUGGER  //uncomment this line to enable the debugger to catch asserts. This line should be commented out on checkin.
#ifdef RUNNING_IN_DEBUGGER
#define REAL_ASSERT std::exit(1);
#else
#define REAL_ASSERT
#endif

#define ASSERT_ENABLED
#if defined ASSERT_ENABLED

    #define Q_ASSERT_CTX_MSG(cond, ctx, msg, ctx_msg) {\
        if(!(cond))\
        {\
            q_assert_body(true, __FILE__, __LINE__, ctx, std::string(msg), std::string(ctx_msg));\
        }\
    }
    #define Q_ASSERT_CTX_MSG_NODUMP(cond, ctx, msg, ctx_msg) {\
        if(!(cond))\
        {\
            q_assert_body(false, __FILE__, __LINE__, ctx, std::string(msg), std::string(ctx_msg));\
        }\
    }

#else
    #define Q_ASSERT_CTX_MSG(cond, ctx, msg, ctx_msg)
    #define Q_ASSERT_CTX_MSG_NODUMP(cond, ctx, msg, ctx_msg)
#endif

#define Q_ASSERT(cond, msg) Q_ASSERT_CTX_MSG(cond, name(), msg, "")
#define Q_ASSERT_NODUMP(cond, msg) Q_ASSERT_CTX_MSG_NODUMP(cond, name(), msg, "")

#define Q_ASSERT_CTX(cond, ctx, msg) Q_ASSERT_CTX_MSG(cond, ctx, msg, "")
#define Q_ASSERT_CTX_NODUMP(cond, ctx, msg) Q_ASSERT_CTX_MSG_NODUMP(cond, ctx, msg, "")

#endif //ASSERT_H
