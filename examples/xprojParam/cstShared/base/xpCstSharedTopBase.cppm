//

// GENERATED_CODE_PARAM --block=xpCstSharedTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpCstShared_xpCstSharedTop.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpCstSharedTopBase : public virtual blockPortBase
{
public:
    virtual ~xpCstSharedTopBase() = default;


    xpCstSharedTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstSharedTopInverted : public virtual blockPortBase
{
public:


    xpCstSharedTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCstSharedTopChannels
{
public:


    xpCstSharedTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpCstSharedTopBase *a, xpCstSharedTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
