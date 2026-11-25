//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsScale --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"

export module uvmRegs_uvmRegsScale.base;
import uvmRegs;
using namespace uvmRegs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class uvmRegsScaleBase : public virtual blockPortBase
{
public:
    virtual ~uvmRegsScaleBase() = default;
    static constexpr auto UVM_REGS_SCALE_W = Config::UVM_REGS_SCALE_W;
    // src ports
    // uvmRegsDataIf->uScale1: Datapath words
    rdy_vld_out< uvmRegsWordSt > out;

    // dst ports
    // uScale0->uvmRegsDataIf: Datapath words
    rdy_vld_in< uvmRegsWordSt > in;
    // uRouter->apbReg: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsScaleBase(std::string name, const char * variant) :
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
    using uvmRegsScaleT = uvmRegsScaleT<Config>;
    using uvmRegsScaleSt = uvmRegsScaleSt<Config>;
};
export template<typename Config>
class uvmRegsScaleInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmRegsDataIf->uScale1: Datapath words
    rdy_vld_in< uvmRegsWordSt > out;

    // dst ports
    // uScale0->uvmRegsDataIf: Datapath words
    rdy_vld_out< uvmRegsWordSt > in;
    // uRouter->apbReg: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsScaleInverted(std::string name) :
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
class uvmRegsScaleChannels
{
public:
    // src ports
    // Datapath words
    rdy_vld_channel< uvmRegsWordSt > out;

    // dst ports
    // Datapath words
    rdy_vld_channel< uvmRegsWordSt > in;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsScaleChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmRegsScaleBase<Config> *a, uvmRegsScaleInverted<Config> *b)
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
