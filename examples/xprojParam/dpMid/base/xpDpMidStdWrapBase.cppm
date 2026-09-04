//

// GENERATED_CODE_PARAM --block=xpDpMidStdWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDpMid_xpDpMidStdWrap.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpDpMidStdWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpDpMidStdWrapBase() = default;


    xpDpMidStdWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDpMidStdWrapInverted : public virtual blockPortBase
{
public:


    xpDpMidStdWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpDpMidStdWrapChannels
{
public:


    xpDpMidStdWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpDpMidStdWrapBase *a, xpDpMidStdWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
