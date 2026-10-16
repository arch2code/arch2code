//

// GENERATED_CODE_PARAM --block=vltTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module vlTiming_vltTop.base;
import vlTiming_vlt;
using namespace vlTiming_vlt_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class vltTopBase : public virtual blockPortBase
{
public:
    virtual ~vltTopBase() = default;


    vltTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class vltTopInverted : public virtual blockPortBase
{
public:


    vltTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class vltTopChannels
{
public:


    vltTopChannels(std::string name, std::string srcName)
    {};
    void bind( vltTopBase *a, vltTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
