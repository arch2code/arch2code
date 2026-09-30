//

// GENERATED_CODE_PARAM --block=xpMtxSrcPar --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpMtxIp_xpMtxSrcPar.base;
import xpMtxIp;
using namespace xpMtxIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpMtxSrcParBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxSrcParBase() = default;
    static constexpr auto MI_SRC_WIDTH = Config::MI_SRC_WIDTH;
    // src ports
    // miSrcParIf->External: Producer port interface, parameterized payload
    push_ack_out< miSrcParSt<Config> > out;


    xpMtxSrcParBase(std::string name, const char * variant) :
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
    using miSrcPixelT = miSrcPixelT<Config>;
    using miSrcParSt = miSrcParSt<Config>;
};
export template<typename Config>
class xpMtxSrcParInverted : public virtual blockPortBase
{
public:
    // src ports
    // miSrcParIf->External: Producer port interface, parameterized payload
    push_ack_in< miSrcParSt<Config> > out;


    xpMtxSrcParInverted(std::string name) :
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
export template<typename Config>
class xpMtxSrcParChannels
{
public:
    // src ports
    // Producer port interface, parameterized payload
    push_ack_channel< miSrcParSt<Config> > out;


    xpMtxSrcParChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpMtxSrcParBase<Config> *a, xpMtxSrcParInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
