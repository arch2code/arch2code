//

// GENERATED_CODE_PARAM --block=xpDeparamTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDeparam_xpDeparamTop.base;
import xpDeparam_xpDeparamTop;
import xpGain;
import xpFilter;
import xpSink;
using namespace xpDeparam_xpDeparamTop_ns;
using namespace xpGain_ns;
using namespace xpFilter_ns;
using namespace xpSink_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpDeparamTopBase : public virtual blockPortBase
{
public:
    virtual ~xpDeparamTopBase() = default;


    xpDeparamTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDeparamTopInverted : public virtual blockPortBase
{
public:


    xpDeparamTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDeparamTopChannels
{
public:


    xpDeparamTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpDeparamTopBase *a, xpDeparamTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
