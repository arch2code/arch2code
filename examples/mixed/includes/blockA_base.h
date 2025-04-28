#ifndef BLOCKA_BASE_H
#define BLOCKA_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"

class blockABase : public virtual blockPortBase
{
public:
    virtual ~blockABase() = default;
    // src ports
    // aStuffIf->uBlockB: An interface for A
    req_ack_out< aSt, aASt > aStuffIf;
    // cStuffIf->uBlockC: An interface for C
    rdy_vld_out< seeSt > cStuffIf;
    // startDone->uBlockB: A start done interface
    notify_ack_out< > startDone;

    // dst ports
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    blockABase(std::string name, const char * variant) :
        aStuffIf("aStuffIf")
        ,cStuffIf("cStuffIf")
        ,startDone("startDone")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        aStuffIf->setTimed(nsec, mode);
        cStuffIf->setTimed(nsec, mode);
        startDone->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        aStuffIf->setLogging(verbosity);
        cStuffIf->setLogging(verbosity);
        startDone->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class blockAInverted : public virtual blockPortBase
{
public:
    // src ports
    // aStuffIf->uBlockB: An interface for A
    req_ack_in< aSt, aASt > aStuffIf;
    // cStuffIf->uBlockC: An interface for C
    rdy_vld_in< seeSt > cStuffIf;
    // startDone->uBlockB: A start done interface
    notify_ack_in< > startDone;

    // dst ports
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    blockAInverted(std::string name) :
        aStuffIf(("aStuffIf"+name).c_str())
        ,cStuffIf(("cStuffIf"+name).c_str())
        ,startDone(("startDone"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        aStuffIf->setTimed(nsec, mode);
        cStuffIf->setTimed(nsec, mode);
        startDone->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        aStuffIf->setLogging(verbosity);
        cStuffIf->setLogging(verbosity);
        startDone->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class blockAChannels
{
public:
    // src ports
    //   aStuffIf
    req_ack_channel< aSt, aASt > aStuffIf;
    //   cStuffIf
    rdy_vld_channel< seeSt > cStuffIf;
    //   startDone
    notify_ack_channel< > startDone;

    // dst ports
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    blockAChannels(std::string name, std::string srcName) :
    aStuffIf(("aStuffIf"+name).c_str(), srcName)
    ,cStuffIf(("cStuffIf"+name).c_str(), srcName)
    ,startDone(("startDone"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( blockABase *a, blockAInverted *b)
    {
        a->aStuffIf( aStuffIf );
        b->aStuffIf( aStuffIf );
        a->cStuffIf( cStuffIf );
        b->cStuffIf( cStuffIf );
        a->startDone( startDone );
        b->startDone( startDone );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif //BLOCKA_BASE_H
