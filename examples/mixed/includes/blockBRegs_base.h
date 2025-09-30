#ifndef BLOCKBREGS_BASE_H
#define BLOCKBREGS_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "memory_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "status_channel.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludeIncludes.h"

class blockBRegsBase : public virtual blockPortBase
{
public:
    virtual ~blockBRegsBase() = default;
    // src ports
    // blockB->mem(blockBTable1) Dual Port with one connection
    memory_out< bSizeSt, seeSt > blockBTable1;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_in< bSizeRegSt > roBsize;


    blockBRegsBase(std::string name, const char * variant) :
        blockBTable1("blockBTable1")
        ,apbReg("apbReg")
        ,roBsize("roBsize")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockBTable1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        blockBTable1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
        roBsize->setLogging(verbosity);
    };
};
class blockBRegsInverted : public virtual blockPortBase
{
public:
    // src ports
    // blockB->mem(blockBTable1) Dual Port with one connection
    memory_in< bSizeSt, seeSt > blockBTable1;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_out< bSizeRegSt > roBsize;


    blockBRegsInverted(std::string name) :
        blockBTable1(("blockBTable1"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
        ,roBsize(("roBsize"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockBTable1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        blockBTable1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
        roBsize->setLogging(verbosity);
    };
};
class blockBRegsChannels
{
public:
    // src ports
    // Dual Port with one connection
    memory_channel< bSizeSt, seeSt > blockBTable1;

    // dst ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg;
    // A Read Only register with a structure that has a definition from an included context
    status_channel< bSizeRegSt > roBsize;


    blockBRegsChannels(std::string name, std::string srcName) :
    blockBTable1(("blockBTable1"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    ,roBsize(("roBsize"+name).c_str(), srcName)
    {};
    void bind( blockBRegsBase *a, blockBRegsInverted *b)
    {
        a->blockBTable1( blockBTable1 );
        b->blockBTable1( blockBTable1 );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
        a->roBsize( roBsize );
        b->roBsize( roBsize );
    };
};

// GENERATED_CODE_END
#endif //BLOCKBREGS_BASE_H
