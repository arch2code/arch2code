//

// GENERATED_CODE_PARAM --block=xpMtxElectTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpMtxElect_xpMtxElectTop.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxElectTopBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxElectTopBase() = default;


    xpMtxElectTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxElectTopInverted : public virtual blockPortBase
{
public:


    xpMtxElectTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxElectTopChannels
{
public:


    xpMtxElectTopChannels(std::string name, std::string srcName) 
    {};
    void bind( xpMtxElectTopBase *a, xpMtxElectTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
