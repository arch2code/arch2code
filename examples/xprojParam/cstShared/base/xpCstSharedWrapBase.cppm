//

// GENERATED_CODE_PARAM --block=xpCstSharedWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstShared_xpCstSharedWrap.base;
import xpCstShared_xpCstSharedDefs;
using namespace xpCstShared_xpCstSharedDefs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpCstSharedWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpCstSharedWrapBase() = default;


    xpCstSharedWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstSharedWrapInverted : public virtual blockPortBase
{
public:


    xpCstSharedWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstSharedWrapChannels
{
public:


    xpCstSharedWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpCstSharedWrapBase *a, xpCstSharedWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
