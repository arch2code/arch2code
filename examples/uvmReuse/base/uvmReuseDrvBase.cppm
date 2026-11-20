//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"

export module uvmReuse_uvmReuseDrv.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseDrvBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseDrvBase() = default;
    // src ports
    // uvmReuseStreamIf->u_uvmReuseChain: Packets, one word per beat
    rdy_vld_out< uvmReuseBeatSt > out;
    // apbReg->u_uvmReuseChain: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseDrvBase(std::string name, const char * variant) :
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
export class uvmReuseDrvInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmReuseStreamIf->u_uvmReuseChain: Packets, one word per beat
    rdy_vld_in< uvmReuseBeatSt > out;
    // apbReg->u_uvmReuseChain: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseDrvInverted(std::string name) :
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
export class uvmReuseDrvChannels
{
public:
    // src ports
    // Packets, one word per beat
    rdy_vld_channel< uvmReuseBeatSt > out;
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseDrvChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmReuseDrvBase *a, uvmReuseDrvInverted *b)
    {
        a->out( out );
        b->out( out );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
