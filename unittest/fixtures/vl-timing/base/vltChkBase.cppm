//

// GENERATED_CODE_PARAM --block=vltChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module vlTiming_vltChk.base;
import vlTiming_vlt;
using namespace vlTiming_vlt_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class vltChkBase : public virtual blockPortBase
{
public:
    virtual ~vltChkBase() = default;
    // dst ports
    // uSrc->vltIf: Single-sample push/ack stream
    push_ack_in< vltSt > in;


    vltChkBase(std::string name, const char * variant) :
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
export class vltChkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uSrc->vltIf: Single-sample push/ack stream
    push_ack_out< vltSt > in;


    vltChkInverted(std::string name) :
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
export class vltChkChannels
{
public:
    // dst ports
    // Single-sample push/ack stream
    push_ack_channel< vltSt > in;


    vltChkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( vltChkBase *a, vltChkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
