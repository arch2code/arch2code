//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"

export module uvmRegs_uvmRegsDrv.base;
import uvmRegs;
using namespace uvmRegs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmRegsDrvBase : public virtual blockPortBase
{
public:
    virtual ~uvmRegsDrvBase() = default;
    // src ports
    // uvmRegsDataIf->u_uvmRegs: Datapath words
    rdy_vld_out< uvmRegsWordSt > out;
    // apbReg->u_uvmRegs: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsDrvBase(std::string name, const char * variant) :
        out("out")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsDrvInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmRegsDataIf->u_uvmRegs: Datapath words
    rdy_vld_in< uvmRegsWordSt > out;
    // apbReg->u_uvmRegs: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsDrvInverted(std::string name) :
        out(("out"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsDrvChannels
{
public:
    // src ports
    // Datapath words
    rdy_vld_channel< uvmRegsWordSt > out;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsDrvChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmRegsDrvBase *a, uvmRegsDrvInverted *b)
    {
        a->out( out );
        b->out( out );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
