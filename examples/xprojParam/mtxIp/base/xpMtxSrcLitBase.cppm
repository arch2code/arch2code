//

// GENERATED_CODE_PARAM --block=xpMtxSrcLit --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpMtxIp_xpMtxSrcLit.base;
import xpMtxIp;
using namespace xpMtxIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxSrcLitBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxSrcLitBase() = default;
    // src ports
    // miSrcLitIf->External: Producer port interface, literal payload
    push_ack_out< miSrcLitSt > out;


    xpMtxSrcLitBase(std::string name, const char * variant) :
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
export class xpMtxSrcLitInverted : public virtual blockPortBase
{
public:
    // src ports
    // miSrcLitIf->External: Producer port interface, literal payload
    push_ack_in< miSrcLitSt > out;


    xpMtxSrcLitInverted(std::string name) :
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
export class xpMtxSrcLitChannels
{
public:
    // src ports
    // Producer port interface, literal payload
    push_ack_channel< miSrcLitSt > out;


    xpMtxSrcLitChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpMtxSrcLitBase *a, xpMtxSrcLitInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
