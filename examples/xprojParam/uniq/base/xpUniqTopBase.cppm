//

// GENERATED_CODE_PARAM --block=xpUniqTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpUniq_xpUniqTop.base;
import xpUniq_xpUniqTop;
import xpGain_xpGainUniq;
import xpFilter_xpFilterUniq;
import xpSink_xpSinkUniq;
using namespace xpUniq_xpUniqTop_ns;
using namespace xpGain_xpGainUniq_ns;
using namespace xpFilter_xpFilterUniq_ns;
using namespace xpSink_xpSinkUniq_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpUniqTopBase : public virtual blockPortBase
{
public:
    virtual ~xpUniqTopBase() = default;


    xpUniqTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpUniqTopInverted : public virtual blockPortBase
{
public:


    xpUniqTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpUniqTopChannels
{
public:


    xpUniqTopChannels(std::string name, std::string srcName) 
    {};
    void bind( xpUniqTopBase *a, xpUniqTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
