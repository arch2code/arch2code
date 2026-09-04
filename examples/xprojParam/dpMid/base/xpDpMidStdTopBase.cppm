//

// GENERATED_CODE_PARAM --block=xpDpMidStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpDpMid_xpDpMidStdTop.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpDpMidStdTopBase : public virtual blockPortBase
{
public:
    virtual ~xpDpMidStdTopBase() = default;


    xpDpMidStdTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDpMidStdTopInverted : public virtual blockPortBase
{
public:


    xpDpMidStdTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDpMidStdTopChannels
{
public:


    xpDpMidStdTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpDpMidStdTopBase *a, xpDpMidStdTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
