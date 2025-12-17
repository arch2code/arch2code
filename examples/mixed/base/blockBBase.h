#ifndef BLOCKB_BASE_H
#define BLOCKB_BASE_H

// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "status_channel.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludeIncludes.h"

class blockBBase : public virtual blockPortBase
{
public:
    virtual ~blockBBase() = default;
    // dst ports
    // uBlockA->aStuffIf: An interface for A
    req_ack_in< aSt, aASt > btod;
    // uBlockA->startDone: A start done interface
    notify_ack_in< > startDone;
    // uBlockA->dupIf: Duplicate interface def
    rdy_vld_in< seeSt > dupIf;
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    blockBBase(std::string name, const char * variant) :
        btod("btod")
        ,startDone("startDone")
        ,dupIf("dupIf")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        btod->setTimed(nsec, mode);
        startDone->setTimed(nsec, mode);
        dupIf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        btod->setLogging(verbosity);
        startDone->setLogging(verbosity);
        dupIf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class blockBInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uBlockA->aStuffIf: An interface for A
    req_ack_out< aSt, aASt > btod;
    // uBlockA->startDone: A start done interface
    notify_ack_out< > startDone;
    // uBlockA->dupIf: Duplicate interface def
    rdy_vld_out< seeSt > dupIf;
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    blockBInverted(std::string name) :
        btod(("btod"+name).c_str())
        ,startDone(("startDone"+name).c_str())
        ,dupIf(("dupIf"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        btod->setTimed(nsec, mode);
        startDone->setTimed(nsec, mode);
        dupIf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        btod->setLogging(verbosity);
        startDone->setLogging(verbosity);
        dupIf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class blockBChannels
{
public:
    // dst ports
    // An interface for A
    req_ack_channel< aSt, aASt > btod;
    // A start done interface
    notify_ack_channel< > startDone;
    // Duplicate interface def
    rdy_vld_channel< seeSt > dupIf;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    blockBChannels(std::string name, std::string srcName) :
    btod(("btod"+name).c_str(), srcName)
    ,startDone(("startDone"+name).c_str(), srcName)
    ,dupIf(("dupIf"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( blockBBase *a, blockBInverted *b)
    {
        a->btod( btod );
        b->btod( btod );
        a->startDone( startDone );
        b->startDone( startDone );
        a->dupIf( dupIf );
        b->dupIf( dupIf );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif // BLOCKB_BASE_H
