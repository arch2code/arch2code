//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nested --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module nested.base;
import nested;
using namespace nested_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class nestedBase : public virtual blockPortBase
{
public:
    virtual ~nestedBase() = default;


    nestedBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class nestedInverted : public virtual blockPortBase
{
public:


    nestedInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class nestedChannels
{
public:


    nestedChannels(std::string name, std::string srcName)
    {};
    void bind( nestedBase *a, nestedInverted *b)
    {
    };
};

// GENERATED_CODE_END
