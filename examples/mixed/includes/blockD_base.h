#ifndef BLOCKD_BASE_H
#define BLOCKD_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludes.h"
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

    // dst ports
    // External->aStuffIf: An interface for A
    req_ack_in< aSt, aASt > btod;


    blockDBase(std::string name, const char * variant) :
        cStuffIf("cStuffIf")
        ,dee0("dee0")
        ,dee1("dee1")
        ,btod("btod")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dee0->setTimed(nsec, mode);
        dee1->setTimed(nsec, mode);
        btod->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dee0->setLogging(verbosity);
        dee1->setLogging(verbosity);
        btod->setLogging(verbosity);
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

    // dst ports
    // External->aStuffIf: An interface for A
    req_ack_out< aSt, aASt > btod;


    blockDInverted(std::string name) :
        cStuffIf(("cStuffIf"+name).c_str())
        ,dee0(("dee0"+name).c_str())
        ,dee1(("dee1"+name).c_str())
        ,btod(("btod"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dee0->setTimed(nsec, mode);
        dee1->setTimed(nsec, mode);
        btod->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dee0->setLogging(verbosity);
        dee1->setLogging(verbosity);
        btod->setLogging(verbosity);
    };
};
class blockDChannels
{
public:
    // src ports
    //   cStuffIf
    rdy_vld_channel< seeSt > cStuffIf;
    //   dStuffIf
    rdy_vld_channel< dSt > dee0;
    //   dStuffIf
    rdy_vld_channel< dSt > dee1;

    // dst ports
    //   aStuffIf
    req_ack_channel< aSt, aASt > btod;


    blockDChannels(std::string name, std::string srcName) :
    cStuffIf(("cStuffIf"+name).c_str(), srcName)
    ,dee0(("dee0"+name).c_str(), srcName)
    ,dee1(("dee1"+name).c_str(), srcName)
    ,btod(("btod"+name).c_str(), srcName)
    {};
    void bind( blockDBase *a, blockDInverted *b)
    {
        a->cStuffIf( cStuffIf );
        b->cStuffIf( cStuffIf );
        a->dee0( dee0 );
        b->dee0( dee0 );
        a->dee1( dee1 );
        b->dee1( dee1 );
        a->btod( btod );
        b->btod( btod );
    };
};

// GENERATED_CODE_END

#endif //BLOCKD_BASE_H
