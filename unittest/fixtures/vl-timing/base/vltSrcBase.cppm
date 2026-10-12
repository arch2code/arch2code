//

// GENERATED_CODE_PARAM --block=vltSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module vlTiming_vltSrc.base;
import vlTiming_vlt;
using namespace vlTiming_vlt_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class vltSrcBase : public virtual blockPortBase
{
public:
    virtual ~vltSrcBase() = default;
    // src ports
    // vltIf->uChk: Single-sample push/ack stream
    push_ack_out< vltSt > out;


    vltSrcBase(std::string name, const char * variant) :
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
export class vltSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // vltIf->uChk: Single-sample push/ack stream
    push_ack_in< vltSt > out;


    vltSrcInverted(std::string name) :
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
export class vltSrcChannels
{
public:
    // src ports
    // Single-sample push/ack stream
    push_ack_channel< vltSt > out;


    vltSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( vltSrcBase *a, vltSrcInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
