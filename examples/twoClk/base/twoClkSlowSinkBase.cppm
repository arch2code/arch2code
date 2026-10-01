//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module twoClk_twoClkSlowSink.base;
import twoClkIp;
using namespace twoClkIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkSlowSinkBase : public virtual blockPortBase
{
public:
    virtual ~twoClkSlowSinkBase() = default;
    // dst ports
    // uSlowTick->twoClkDataIf: twoClkIpSrc -> assembler sink data stream
    push_ack_in< twoClkDataSt > in;


    twoClkSlowSinkBase(std::string name, const char * variant) :
        in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        in->setLogging(verbosity);
    };
};
export class twoClkSlowSinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uSlowTick->twoClkDataIf: twoClkIpSrc -> assembler sink data stream
    push_ack_out< twoClkDataSt > in;


    twoClkSlowSinkInverted(std::string name) :
        in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        in->setLogging(verbosity);
    };
};
export class twoClkSlowSinkChannels
{
public:
    // dst ports
    // twoClkIpSrc -> assembler sink data stream
    push_ack_channel< twoClkDataSt > in;


    twoClkSlowSinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( twoClkSlowSinkBase *a, twoClkSlowSinkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
