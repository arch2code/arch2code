//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"

export module uvmReuseLeaf.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class uvmReuseLeafBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseLeafBase() = default;
    static constexpr auto UVM_REUSE_OFF_W = Config::UVM_REUSE_OFF_W;
    // src ports
    // uvmReuseStreamIf->uSink: Packets, one word per beat
    rdy_vld_out< uvmReuseBeatSt > out;

    // dst ports
    // uSrc->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_in< uvmReuseBeatSt > in;
    // uRouter->apbReg: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafBase(std::string name, const char * variant) :
        out("out")
        ,in("in")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
    using uvmReuseOffT = uvmReuseOffT<Config>;
    using uvmReuseOffSt = uvmReuseOffSt<Config>;
};
export template<typename Config>
class uvmReuseLeafInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmReuseStreamIf->uSink: Packets, one word per beat
    rdy_vld_in< uvmReuseBeatSt > out;

    // dst ports
    // uSrc->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_out< uvmReuseBeatSt > in;
    // uRouter->apbReg: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafInverted(std::string name) :
        out(("out"+name).c_str())
        ,in(("in"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export template<typename Config>
class uvmReuseLeafChannels
{
public:
    // src ports
    // Packets, one word per beat
    rdy_vld_channel< uvmReuseBeatSt > out;

    // dst ports
    // Packets, one word per beat
    rdy_vld_channel< uvmReuseBeatSt > in;
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmReuseLeafBase<Config> *a, uvmReuseLeafInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
