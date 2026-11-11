//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMemSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module uvmMem_uvmMemSrc.base;
import uvmMem;
using namespace uvmMem_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmMemSrcBase : public virtual blockPortBase
{
public:
    virtual ~uvmMemSrcBase() = default;
    // src ports
    // uvmMemCmdIf->u_uvmMem: Copy commands
    rdy_vld_out< uvmMemCmdSt > cmd;


    uvmMemSrcBase(std::string name, const char * variant) :
        cmd("cmd")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cmd->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cmd->setLogging(verbosity);
    };
};
export class uvmMemSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmMemCmdIf->u_uvmMem: Copy commands
    rdy_vld_in< uvmMemCmdSt > cmd;


    uvmMemSrcInverted(std::string name) :
        cmd(("cmd"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cmd->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cmd->setLogging(verbosity);
    };
};
export class uvmMemSrcChannels
{
public:
    // src ports
    // Copy commands
    rdy_vld_channel< uvmMemCmdSt > cmd;


    uvmMemSrcChannels(std::string name, std::string srcName) :
    cmd(("cmd"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( uvmMemSrcBase *a, uvmMemSrcInverted *b)
    {
        a->cmd( cmd );
        b->cmd( cmd );
    };
};

// GENERATED_CODE_END
