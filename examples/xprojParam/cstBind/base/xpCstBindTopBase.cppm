//

// GENERATED_CODE_PARAM --block=xpCstBindTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpCstBind_xpCstBindTop.base;
import xpCstBind_xpCstBindTop;
using namespace xpCstBind_xpCstBindTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpCstBindTopBase : public virtual blockPortBase
{
public:
    virtual ~xpCstBindTopBase() = default;


    xpCstBindTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstBindTopInverted : public virtual blockPortBase
{
public:


    xpCstBindTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstBindTopChannels
{
public:


    xpCstBindTopChannels(std::string name, std::string srcName) 
    {};
    void bind( xpCstBindTopBase *a, xpCstBindTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
