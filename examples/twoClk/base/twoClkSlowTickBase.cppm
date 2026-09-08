//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowTick --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module twoClk_twoClkSlowTick.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkSlowTickBase : public virtual blockPortBase
{
public:
    virtual ~twoClkSlowTickBase() = default;


    twoClkSlowTickBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class twoClkSlowTickInverted : public virtual blockPortBase
{
public:


    twoClkSlowTickInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class twoClkSlowTickChannels
{
public:


    twoClkSlowTickChannels(std::string name, std::string srcName) 
    {};
    void bind( twoClkSlowTickBase *a, twoClkSlowTickInverted *b)
    {
    };
};

// GENERATED_CODE_END
