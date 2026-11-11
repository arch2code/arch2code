//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "memory_channel.h"
#include "rdy_vld_channel.h"

export module uvmMem.base;
import uvmMem;
using namespace uvmMem_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmMemBase : public virtual blockPortBase
{
public:
    virtual ~uvmMemBase() = default;
    // src ports
    // uvmMemWordIf->uSink: Words read back
    rdy_vld_out< uvmMemWordSt > out;
    // uvmMemPortIf->uStore: One port of the shared memory
    memory_out< uvmMemAddrSt, uvmMemWordSt > wr;
    // uvmMemPortIf->uStore: One port of the shared memory
    memory_out< uvmMemAddrSt, uvmMemWordSt > rd;

    // dst ports
    // uSrc->uvmMemCmdIf: Copy commands
    rdy_vld_in< uvmMemCmdSt > cmd;


    uvmMemBase(std::string name, const char * variant) :
        out("out")
        ,wr("wr")
        ,rd("rd")
        ,cmd("cmd")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        wr->setTimed(nsec, mode);
        rd->setTimed(nsec, mode);
        cmd->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        wr->setLogging(verbosity);
        rd->setLogging(verbosity);
        cmd->setLogging(verbosity);
    };
};
export class uvmMemInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmMemWordIf->uSink: Words read back
    rdy_vld_in< uvmMemWordSt > out;
    // uvmMemPortIf->uStore: One port of the shared memory
    memory_in< uvmMemAddrSt, uvmMemWordSt > wr;
    // uvmMemPortIf->uStore: One port of the shared memory
    memory_in< uvmMemAddrSt, uvmMemWordSt > rd;

    // dst ports
    // uSrc->uvmMemCmdIf: Copy commands
    rdy_vld_out< uvmMemCmdSt > cmd;


    uvmMemInverted(std::string name) :
        out(("out"+name).c_str())
        ,wr(("wr"+name).c_str())
        ,rd(("rd"+name).c_str())
        ,cmd(("cmd"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        wr->setTimed(nsec, mode);
        rd->setTimed(nsec, mode);
        cmd->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        wr->setLogging(verbosity);
        rd->setLogging(verbosity);
        cmd->setLogging(verbosity);
    };
};
export class uvmMemChannels
{
public:
    // src ports
    // Words read back
    rdy_vld_channel< uvmMemWordSt > out;
    // One port of the shared memory
    memory_channel< uvmMemAddrSt, uvmMemWordSt > wr;
    // One port of the shared memory
    memory_channel< uvmMemAddrSt, uvmMemWordSt > rd;

    // dst ports
    // Copy commands
    rdy_vld_channel< uvmMemCmdSt > cmd;


    uvmMemChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,wr(("wr"+name).c_str(), srcName)
    ,rd(("rd"+name).c_str(), srcName)
    ,cmd(("cmd"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( uvmMemBase *a, uvmMemInverted *b)
    {
        a->out( out );
        b->out( out );
        a->wr( wr );
        b->wr( wr );
        a->rd( rd );
        b->rd( rd );
        a->cmd( cmd );
        b->cmd( cmd );
    };
};

// GENERATED_CODE_END
