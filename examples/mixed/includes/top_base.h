#ifndef TOP_BASE_H
#define TOP_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"

class topBase : public virtual blockPortBase
{
public:
    virtual ~topBase() = default;


    topBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class topInverted : public virtual blockPortBase
{
public:


    topInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class topChannels
{
public:


    topChannels(std::string name, std::string srcName) 
    {};
    void bind( topBase *a, topInverted *b)
    {
    };
};

// GENERATED_CODE_END

#endif //TOP_BASE_H
