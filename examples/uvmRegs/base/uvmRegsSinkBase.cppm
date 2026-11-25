//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module uvmRegs_uvmRegsSink.base;
import uvmRegs;
using namespace uvmRegs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmRegsSinkBase : public virtual blockPortBase
{
public:
    virtual ~uvmRegsSinkBase() = default;
    // dst ports
    // u_uvmRegs->uvmRegsDataIf: Datapath words
    rdy_vld_in< uvmRegsWordSt > in;


    uvmRegsSinkBase(std::string name, const char * variant) :
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
export class uvmRegsSinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // u_uvmRegs->uvmRegsDataIf: Datapath words
    rdy_vld_out< uvmRegsWordSt > in;


    uvmRegsSinkInverted(std::string name) :
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
export class uvmRegsSinkChannels
{
public:
    // dst ports
    // Datapath words
    rdy_vld_channel< uvmRegsWordSt > in;


    uvmRegsSinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( uvmRegsSinkBase *a, uvmRegsSinkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
