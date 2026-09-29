//

// GENERATED_CODE_PARAM --block=xpCstUseWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstUse_xpCstUseWrap.base;
import xpCstIp;
import xpCstUse_xpCstUseTop;
using namespace xpCstIp_ns;
using namespace xpCstUse_xpCstUseTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpCstUseWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpCstUseWrapBase() = default;


    xpCstUseWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstUseWrapInverted : public virtual blockPortBase
{
public:


    xpCstUseWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstUseWrapChannels
{
public:


    xpCstUseWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpCstUseWrapBase *a, xpCstUseWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
