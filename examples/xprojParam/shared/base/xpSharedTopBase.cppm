//

// GENERATED_CODE_PARAM --block=xpSharedTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpShared_xpSharedTop.base;
import xpGain;
using namespace xpGain_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpSharedTopBase : public virtual blockPortBase
{
public:
    virtual ~xpSharedTopBase() = default;


    xpSharedTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpSharedTopInverted : public virtual blockPortBase
{
public:


    xpSharedTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpSharedTopChannels
{
public:


    xpSharedTopChannels(std::string name, std::string srcName) 
    {};
    void bind( xpSharedTopBase *a, xpSharedTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
