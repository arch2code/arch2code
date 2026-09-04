//

// GENERATED_CODE_PARAM --block=xpCstBindWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstBind_xpCstBindWrap.base;
import xpCstIp;
import xpCstBind_xpCstSup;
using namespace xpCstIp_ns;
using namespace xpCstBind_xpCstSup_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpCstBindWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpCstBindWrapBase() = default;


    xpCstBindWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstBindWrapInverted : public virtual blockPortBase
{
public:


    xpCstBindWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstBindWrapChannels
{
public:


    xpCstBindWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpCstBindWrapBase *a, xpCstBindWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
