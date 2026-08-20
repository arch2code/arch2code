//

// GENERATED_CODE_PARAM --block=xpMtxDstLit --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpMtxIp_xpMtxDstLit.base;
import xpMtxIp;
using namespace xpMtxIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxDstLitBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxDstLitBase() = default;
    // dst ports
    // External->miDstLitIf: Consumer port interface, literal payload
    push_ack_in< miDstLitSt > in;


    xpMtxDstLitBase(std::string name, const char * variant) :
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
export class xpMtxDstLitInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->miDstLitIf: Consumer port interface, literal payload
    push_ack_out< miDstLitSt > in;


    xpMtxDstLitInverted(std::string name) :
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
export class xpMtxDstLitChannels
{
public:
    // dst ports
    // Consumer port interface, literal payload
    push_ack_channel< miDstLitSt > in;


    xpMtxDstLitChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpMtxDstLitBase *a, xpMtxDstLitInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
