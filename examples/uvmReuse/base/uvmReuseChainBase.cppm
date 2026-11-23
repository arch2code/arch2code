//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"

export module uvmReuse_uvmReuseChain.base;
import uvmReuseLeaf;
import uvmReuse;
using namespace uvmReuseLeaf_ns;
using namespace uvmReuse_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class uvmReuseChainBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseChainBase() = default;
    static constexpr auto UVM_REUSE_B_W = Config::UVM_REUSE_B_W;
    // src ports
    // uvmReuseStreamIf->uSink: Packets, one word per beat
    rdy_vld_out< uvmReuseBeatSt > out;

    // dst ports
    // uDrv->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_in< uvmReuseBeatSt > in;
    // uDrv->apbReg: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseChainBase(std::string name, const char * variant) :
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
};
export template<typename Config>
class uvmReuseChainInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmReuseStreamIf->uSink: Packets, one word per beat
    rdy_vld_in< uvmReuseBeatSt > out;

    // dst ports
    // uDrv->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_out< uvmReuseBeatSt > in;
    // uDrv->apbReg: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseChainInverted(std::string name) :
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
class uvmReuseChainChannels
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


    uvmReuseChainChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmReuseChainBase<Config> *a, uvmReuseChainInverted<Config> *b)
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
