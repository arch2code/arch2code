//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"

export module uvmRegs.base;
import uvmRegs;
using namespace uvmRegs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmRegsBase : public virtual blockPortBase
{
public:
    virtual ~uvmRegsBase() = default;
    // src ports
    // uvmRegsDataIf->uSink: Datapath words
    rdy_vld_out< uvmRegsWordSt > out;

    // dst ports
    // uDrv->uvmRegsDataIf: Datapath words
    rdy_vld_in< uvmRegsWordSt > in;
    // uDrv->apbReg: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsBase(std::string name, const char * variant) :
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
export class uvmRegsInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmRegsDataIf->uSink: Datapath words
    rdy_vld_in< uvmRegsWordSt > out;

    // dst ports
    // uDrv->uvmRegsDataIf: Datapath words
    rdy_vld_out< uvmRegsWordSt > in;
    // uDrv->apbReg: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsInverted(std::string name) :
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
export class uvmRegsChannels
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


    uvmRegsChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmRegsBase *a, uvmRegsInverted *b)
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
