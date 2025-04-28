#ifndef BLOCKB_BASE_H
#define BLOCKB_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludes.h"
#include "mixedIncludeIncludes.h"

class blockBBase : public virtual blockPortBase
{
public:
    virtual ~blockBBase() = default;
    // src ports

    // dst ports
    // uBlockA->aStuffIf: An interface for A
    req_ack_in< aSt, aASt > btod;
    // uBlockA->startDone: A start done interface
    notify_ack_in< > startDone;
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    blockBBase(std::string name, const char * variant) :
        btod("btod")
        ,startDone("startDone")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        btod->setTimed(nsec, mode);
        startDone->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        btod->setLogging(verbosity);
        startDone->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class blockBInverted : public virtual blockPortBase
{
public:
    // src ports

    // dst ports
    // uBlockA->aStuffIf: An interface for A
    req_ack_out< aSt, aASt > btod;
    // uBlockA->startDone: A start done interface
    notify_ack_out< > startDone;
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    blockBInverted(std::string name) :
        btod(("btod"+name).c_str())
        ,startDone(("startDone"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        btod->setTimed(nsec, mode);
        startDone->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        btod->setLogging(verbosity);
        startDone->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class blockBChannels
{
public:
    // src ports

    // dst ports
    //   aStuffIf
    req_ack_channel< aSt, aASt > btod;
    //   startDone
    notify_ack_channel< > startDone;
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    blockBChannels(std::string name, std::string srcName) :
    btod(("btod"+name).c_str(), srcName)
    ,startDone(("startDone"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( blockBBase *a, blockBInverted *b)
    {
        a->btod( btod );
        b->btod( btod );
        a->startDone( startDone );
        b->startDone( startDone );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif //BLOCKB_BASE_H
