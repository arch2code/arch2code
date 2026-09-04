//

// GENERATED_CODE_PARAM --block=xpInhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpInhVar_xpInhTop.base;
import xpInhVar_xpInhCont;
using namespace xpInhVar_xpInhCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpInhTopBase : public virtual blockPortBase
{
public:
    virtual ~xpInhTopBase() = default;


    xpInhTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpInhTopInverted : public virtual blockPortBase
{
public:


    xpInhTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpInhTopChannels
{
public:


    xpInhTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpInhTopBase *a, xpInhTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
