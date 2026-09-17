//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkConsumer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module clkGen_clkConsumer.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class clkConsumerBase : public virtual blockPortBase
{
public:
    virtual ~clkConsumerBase() = default;


    clkConsumerBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class clkConsumerInverted : public virtual blockPortBase
{
public:


    clkConsumerInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class clkConsumerChannels
{
public:


    clkConsumerChannels(std::string name, std::string srcName) 
    {};
    void bind( clkConsumerBase *a, clkConsumerInverted *b)
    {
    };
};

// GENERATED_CODE_END
