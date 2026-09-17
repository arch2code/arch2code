//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkDivider --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module clkGen_clkDivider.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class clkDividerBase : public virtual blockPortBase
{
public:
    virtual ~clkDividerBase() = default;


    clkDividerBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class clkDividerInverted : public virtual blockPortBase
{
public:


    clkDividerInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class clkDividerChannels
{
public:


    clkDividerChannels(std::string name, std::string srcName) 
    {};
    void bind( clkDividerBase *a, clkDividerInverted *b)
    {
    };
};

// GENERATED_CODE_END
