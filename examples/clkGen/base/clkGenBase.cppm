//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module clkGen.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class clkGenBase : public virtual blockPortBase
{
public:
    virtual ~clkGenBase() = default;


    clkGenBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class clkGenInverted : public virtual blockPortBase
{
public:


    clkGenInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class clkGenChannels
{
public:


    clkGenChannels(std::string name, std::string srcName) 
    {};
    void bind( clkGenBase *a, clkGenInverted *b)
    {
    };
};

// GENERATED_CODE_END
