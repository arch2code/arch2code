//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module twoClk_twoClkSink.base;
import twoClkIp;
using namespace twoClkIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkSinkBase : public virtual blockPortBase
{
public:
    virtual ~twoClkSinkBase() = default;
    // dst ports
    // uIpSrc->twoClkDataIf: twoClkIpSrc -> assembler sink data stream
    push_ack_in< twoClkDataSt > in;


    twoClkSinkBase(std::string name, const char * variant) :
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
export class twoClkSinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uIpSrc->twoClkDataIf: twoClkIpSrc -> assembler sink data stream
    push_ack_out< twoClkDataSt > in;


    twoClkSinkInverted(std::string name) :
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
export class twoClkSinkChannels
{
public:
    // dst ports
    // twoClkIpSrc -> assembler sink data stream
    push_ack_channel< twoClkDataSt > in;


    twoClkSinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( twoClkSinkBase *a, twoClkSinkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
