//

// GENERATED_CODE_PARAM --block=xpMtxLitTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpMtxLit_xpMtxLitTop.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxLitTopBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxLitTopBase() = default;


    xpMtxLitTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxLitTopInverted : public virtual blockPortBase
{
public:


    xpMtxLitTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxLitTopChannels
{
public:


    xpMtxLitTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpMtxLitTopBase *a, xpMtxLitTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
