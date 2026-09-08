//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkIpSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module twoClkIp_twoClkIpSrc.base;
import twoClkIp;
using namespace twoClkIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkIpSrcBase : public virtual blockPortBase
{
public:
    virtual ~twoClkIpSrcBase() = default;
    // src ports
    // twoClkDataIf->External: twoClkIpSrc -> assembler sink data stream
    push_ack_out< twoClkDataSt > out;


    twoClkIpSrcBase(std::string name, const char * variant) :
        out("out")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
    };
};
export class twoClkIpSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // twoClkDataIf->External: twoClkIpSrc -> assembler sink data stream
    push_ack_in< twoClkDataSt > out;


    twoClkIpSrcInverted(std::string name) :
        out(("out"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
    };
};
export class twoClkIpSrcChannels
{
public:
    // src ports
    // twoClkIpSrc -> assembler sink data stream
    push_ack_channel< twoClkDataSt > out;


    twoClkIpSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( twoClkIpSrcBase *a, twoClkIpSrcInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
