//

// GENERATED_CODE_PARAM --block=xpDpTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpDpTop.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpDpTopBase : public virtual blockPortBase
{
public:
    virtual ~xpDpTopBase() = default;


    xpDpTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDpTopInverted : public virtual blockPortBase
{
public:


    xpDpTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDpTopChannels
{
public:


    xpDpTopChannels(std::string name, std::string srcName) 
    {};
    void bind( xpDpTopBase *a, xpDpTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
