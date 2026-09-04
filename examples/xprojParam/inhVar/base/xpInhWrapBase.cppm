//

// GENERATED_CODE_PARAM --block=xpInhWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpInhVar_xpInhWrap.base;
import xpInhVar_xpInhCont;
using namespace xpInhVar_xpInhCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpInhWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpInhWrapBase() = default;


    xpInhWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpInhWrapInverted : public virtual blockPortBase
{
public:


    xpInhWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpInhWrapChannels
{
public:


    xpInhWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpInhWrapBase *a, xpInhWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
