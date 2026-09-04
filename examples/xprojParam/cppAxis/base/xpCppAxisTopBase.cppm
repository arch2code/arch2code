//

// GENERATED_CODE_PARAM --block=xpCppAxisTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCppAxis_xpCppAxisTop.base;
import xpCppAxis_xpCppAxisTop;
import xpCppAxis_xpCppWrap;
using namespace xpCppAxis_xpCppAxisTop_ns;
using namespace xpCppAxis_xpCppWrap_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpCppAxisTopBase : public virtual blockPortBase
{
public:
    virtual ~xpCppAxisTopBase() = default;


    xpCppAxisTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCppAxisTopInverted : public virtual blockPortBase
{
public:


    xpCppAxisTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpCppAxisTopChannels
{
public:


    xpCppAxisTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpCppAxisTopBase *a, xpCppAxisTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
