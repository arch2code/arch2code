//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module twoClk.base;
import twoClkIp;
using namespace twoClkIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkBase : public virtual blockPortBase
{
public:
    virtual ~twoClkBase() = default;


    twoClkBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class twoClkInverted : public virtual blockPortBase
{
public:


    twoClkInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class twoClkChannels
{
public:


    twoClkChannels(std::string name, std::string srcName) 
    {};
    void bind( twoClkBase *a, twoClkInverted *b)
    {
    };
};

// GENERATED_CODE_END
