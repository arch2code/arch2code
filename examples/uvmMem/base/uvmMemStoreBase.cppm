//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMemStore --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "memory_channel.h"

export module uvmMem_uvmMemStore.base;
import uvmMem;
using namespace uvmMem_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmMemStoreBase : public virtual blockPortBase
{
public:
    virtual ~uvmMemStoreBase() = default;
    // dst ports
    // u_uvmMem->uvmMemPortIf: One port of the shared memory
    memory_in< uvmMemAddrSt, uvmMemWordSt > wr;
    // u_uvmMem->uvmMemPortIf: One port of the shared memory
    memory_in< uvmMemAddrSt, uvmMemWordSt > rd;


    uvmMemStoreBase(std::string name, const char * variant) :
        wr("wr")
        ,rd("rd")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        wr->setTimed(nsec, mode);
        rd->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        wr->setLogging(verbosity);
        rd->setLogging(verbosity);
    };
};
export class uvmMemStoreInverted : public virtual blockPortBase
{
public:
    // dst ports
    // u_uvmMem->uvmMemPortIf: One port of the shared memory
    memory_out< uvmMemAddrSt, uvmMemWordSt > wr;
    // u_uvmMem->uvmMemPortIf: One port of the shared memory
    memory_out< uvmMemAddrSt, uvmMemWordSt > rd;


    uvmMemStoreInverted(std::string name) :
        wr(("wr"+name).c_str())
        ,rd(("rd"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        wr->setTimed(nsec, mode);
        rd->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        wr->setLogging(verbosity);
        rd->setLogging(verbosity);
    };
};
export class uvmMemStoreChannels
{
public:
    // dst ports
    // One port of the shared memory
    memory_channel< uvmMemAddrSt, uvmMemWordSt > wr;
    // One port of the shared memory
    memory_channel< uvmMemAddrSt, uvmMemWordSt > rd;


    uvmMemStoreChannels(std::string name, std::string srcName) :
    wr(("wr"+name).c_str(), srcName)
    ,rd(("rd"+name).c_str(), srcName)
    {};
    void bind( uvmMemStoreBase *a, uvmMemStoreInverted *b)
    {
        a->wr( wr );
        b->wr( wr );
        a->rd( rd );
        b->rd( rd );
    };
};

// GENERATED_CODE_END
