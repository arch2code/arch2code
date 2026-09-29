//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "push_ack_channel.h"

export module ipBridge_bridgeStdTop.base;
import ipBridge;
import common_shared_types;
using namespace ipBridge_ns;
using namespace common_shared_types_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class bridgeStdTopBase : public virtual blockPortBase
{
public:
    virtual ~bridgeStdTopBase() = default;


    bridgeStdTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class bridgeStdTopInverted : public virtual blockPortBase
{
public:


    bridgeStdTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class bridgeStdTopChannels
{
public:


    bridgeStdTopChannels(std::string name, std::string srcName)
    {};
    void bind( bridgeStdTopBase *a, bridgeStdTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
