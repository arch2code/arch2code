//

// GENERATED_CODE_PARAM --block=xpCstUseTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpCstUse_xpCstUseTop.base;
import xpCstUse_xpCstUseTop;
using namespace xpCstUse_xpCstUseTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpCstUseTopBase : public virtual blockPortBase
{
public:
    virtual ~xpCstUseTopBase() = default;


    xpCstUseTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstUseTopInverted : public virtual blockPortBase
{
public:


    xpCstUseTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstUseTopChannels
{
public:


    xpCstUseTopChannels(std::string name, std::string srcName) 
    {};
    void bind( xpCstUseTopBase *a, xpCstUseTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
