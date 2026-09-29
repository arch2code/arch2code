//

// GENERATED_CODE_PARAM --block=xpMtxElectWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpMtxElect_xpMtxElectWrap.base;
import xpMtxIp;
using namespace xpMtxIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxElectWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxElectWrapBase() = default;


    xpMtxElectWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxElectWrapInverted : public virtual blockPortBase
{
public:


    xpMtxElectWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxElectWrapChannels
{
public:


    xpMtxElectWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpMtxElectWrapBase *a, xpMtxElectWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
