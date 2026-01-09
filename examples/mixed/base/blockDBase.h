#ifndef BLOCKD_BASE_H
#define BLOCKD_BASE_H

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "memory_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "status_channel.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludeIncludes.h"

class blockDBase : public virtual blockPortBase
{
public:
    virtual ~blockDBase() = default;
    // src ports
    // cStuffIf->uThreeCs: An interface for C
    rdy_vld_out< seeSt > cStuffIf;
    // dStuffIf->uBlockF0: An interface for D
    rdy_vld_out< dSt > dee0;
    // dStuffIf->uBlockF1: An interface for D
    rdy_vld_out< dSt > dee1;
    // dStuffIf->uBlockF0: An interface for D
    rdy_vld_out< dSt > outD;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_out< bSizeRegSt > roBsize;
    // blockB->mem(blockBTable1) Dual Port with one connection
    memory_out< bSizeSt, bigSt > blockBTable1;
    // blockB->mem(blockBTableSP) Single Port with connection
    memory_out< bSizeSt, nestedSt > blockBTableSP;

    // dst ports
    // uBlockF1->dStuffIf: An interface for D
    rdy_vld_in< dSt > inD;
    // External->aStuffIf: An interface for A
    req_ack_in< aSt, aASt > btod;
    // blockB->reg(rwD) A Read Write register
    status_in< dRegSt > rwD;
    // blockB->reg(blockBTableExt) Memory register - firmware accessible memory-mapped storage
    memory_in< bSizeSt, seeSt > blockBTableExt;


    blockDBase(std::string name, const char * variant) :
        cStuffIf("cStuffIf")
        ,dee0("dee0")
        ,dee1("dee1")
        ,outD("outD")
        ,roBsize("roBsize")
        ,blockBTable1("blockBTable1")
        ,blockBTableSP("blockBTableSP")
        ,inD("inD")
        ,btod("btod")
        ,rwD("rwD")
        ,blockBTableExt("blockBTableExt")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dee0->setTimed(nsec, mode);
        dee1->setTimed(nsec, mode);
        outD->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        blockBTable1->setTimed(nsec, mode);
        blockBTableSP->setTimed(nsec, mode);
        inD->setTimed(nsec, mode);
        btod->setTimed(nsec, mode);
        rwD->setTimed(nsec, mode);
        blockBTableExt->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dee0->setLogging(verbosity);
        dee1->setLogging(verbosity);
        outD->setLogging(verbosity);
        roBsize->setLogging(verbosity);
        blockBTable1->setLogging(verbosity);
        blockBTableSP->setLogging(verbosity);
        inD->setLogging(verbosity);
        btod->setLogging(verbosity);
        rwD->setLogging(verbosity);
        blockBTableExt->setLogging(verbosity);
    };
};
class blockDInverted : public virtual blockPortBase
{
public:
    // src ports
    // cStuffIf->uThreeCs: An interface for C
    rdy_vld_in< seeSt > cStuffIf;
    // dStuffIf->uBlockF0: An interface for D
    rdy_vld_in< dSt > dee0;
    // dStuffIf->uBlockF1: An interface for D
    rdy_vld_in< dSt > dee1;
    // dStuffIf->uBlockF0: An interface for D
    rdy_vld_in< dSt > outD;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_in< bSizeRegSt > roBsize;
    // blockB->mem(blockBTable1) Dual Port with one connection
    memory_in< bSizeSt, bigSt > blockBTable1;
    // blockB->mem(blockBTableSP) Single Port with connection
    memory_in< bSizeSt, nestedSt > blockBTableSP;

    // dst ports
    // uBlockF1->dStuffIf: An interface for D
    rdy_vld_out< dSt > inD;
    // External->aStuffIf: An interface for A
    req_ack_out< aSt, aASt > btod;
    // blockB->reg(rwD) A Read Write register
    status_out< dRegSt > rwD;
    // blockB->reg(blockBTableExt) Memory register - firmware accessible memory-mapped storage
    memory_out< bSizeSt, seeSt > blockBTableExt;


    blockDInverted(std::string name) :
        cStuffIf(("cStuffIf"+name).c_str())
        ,dee0(("dee0"+name).c_str())
        ,dee1(("dee1"+name).c_str())
        ,outD(("outD"+name).c_str())
        ,roBsize(("roBsize"+name).c_str())
        ,blockBTable1(("blockBTable1"+name).c_str())
        ,blockBTableSP(("blockBTableSP"+name).c_str())
        ,inD(("inD"+name).c_str())
        ,btod(("btod"+name).c_str())
        ,rwD(("rwD"+name).c_str())
        ,blockBTableExt(("blockBTableExt"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dee0->setTimed(nsec, mode);
        dee1->setTimed(nsec, mode);
        outD->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        blockBTable1->setTimed(nsec, mode);
        blockBTableSP->setTimed(nsec, mode);
        inD->setTimed(nsec, mode);
        btod->setTimed(nsec, mode);
        rwD->setTimed(nsec, mode);
        blockBTableExt->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dee0->setLogging(verbosity);
        dee1->setLogging(verbosity);
        outD->setLogging(verbosity);
        roBsize->setLogging(verbosity);
        blockBTable1->setLogging(verbosity);
        blockBTableSP->setLogging(verbosity);
        inD->setLogging(verbosity);
        btod->setLogging(verbosity);
        rwD->setLogging(verbosity);
        blockBTableExt->setLogging(verbosity);
    };
};
class blockDChannels
{
public:
    // src ports
    // An interface for C
    rdy_vld_channel< seeSt > cStuffIf;
    // An interface for D
    rdy_vld_channel< dSt > dee0;
    // An interface for D
    rdy_vld_channel< dSt > dee1;
    // An interface for D
    rdy_vld_channel< dSt > outD;
    // A Read Only register with a structure that has a definition from an included context
    status_channel< bSizeRegSt > roBsize;
    // Dual Port with one connection
    memory_channel< bSizeSt, bigSt > blockBTable1;
    // Single Port with connection
    memory_channel< bSizeSt, nestedSt > blockBTableSP;

    // dst ports
    // An interface for D
    rdy_vld_channel< dSt > inD;
    // An interface for A
    req_ack_channel< aSt, aASt > btod;
    // A Read Write register
    status_channel< dRegSt > rwD;
    // Memory register - firmware accessible memory-mapped storage
    memory_channel< bSizeSt, seeSt > blockBTableExt;


    blockDChannels(std::string name, std::string srcName) :
    cStuffIf(("cStuffIf"+name).c_str(), srcName)
    ,dee0(("dee0"+name).c_str(), srcName)
    ,dee1(("dee1"+name).c_str(), srcName)
    ,outD(("outD"+name).c_str(), srcName)
    ,roBsize(("roBsize"+name).c_str(), srcName)
    ,blockBTable1(("blockBTable1"+name).c_str(), srcName)
    ,blockBTableSP(("blockBTableSP"+name).c_str(), srcName)
    ,inD(("inD"+name).c_str(), srcName)
    ,btod(("btod"+name).c_str(), srcName)
    ,rwD(("rwD"+name).c_str(), srcName)
    ,blockBTableExt(("blockBTableExt"+name).c_str(), srcName)
    {};
    void bind( blockDBase *a, blockDInverted *b)
    {
        a->cStuffIf( cStuffIf );
        b->cStuffIf( cStuffIf );
        a->dee0( dee0 );
        b->dee0( dee0 );
        a->dee1( dee1 );
        b->dee1( dee1 );
        a->outD( outD );
        b->outD( outD );
        a->roBsize( roBsize );
        b->roBsize( roBsize );
        a->blockBTable1( blockBTable1 );
        b->blockBTable1( blockBTable1 );
        a->blockBTableSP( blockBTableSP );
        b->blockBTableSP( blockBTableSP );
        a->inD( inD );
        b->inD( inD );
        a->btod( btod );
        b->btod( btod );
        a->rwD( rwD );
        b->rwD( rwD );
        a->blockBTableExt( blockBTableExt );
        b->blockBTableExt( blockBTableExt );
    };
};

// GENERATED_CODE_END

#endif // BLOCKD_BASE_H
