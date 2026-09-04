//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module simple.base;
import simple;
using namespace simple_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class simpleBase : public virtual blockPortBase
{
public:
    virtual ~simpleBase() = default;


    simpleBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class simpleInverted : public virtual blockPortBase
{
public:


    simpleInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class simpleChannels
{
public:


    simpleChannels(std::string name, std::string srcName)
    {};
    void bind( simpleBase *a, simpleInverted *b)
    {
    };
};

// GENERATED_CODE_END
