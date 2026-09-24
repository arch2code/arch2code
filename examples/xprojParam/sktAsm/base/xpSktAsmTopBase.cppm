//

// GENERATED_CODE_PARAM --block=xpSktAsmTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpSktAsm_xpSktAsmTop.base;
import xpSktIp;
import xpSktAsm_xpSktAsmTop;
using namespace xpSktIp_ns;
using namespace xpSktAsm_xpSktAsmTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpSktAsmTopBase : public virtual blockPortBase
{
public:
    virtual ~xpSktAsmTopBase() = default;


    xpSktAsmTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpSktAsmTopInverted : public virtual blockPortBase
{
public:


    xpSktAsmTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpSktAsmTopChannels
{
public:


    xpSktAsmTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpSktAsmTopBase *a, xpSktAsmTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
