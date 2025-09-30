#ifndef BLOCKF_BASE_H
#define BLOCKF_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "status_channel.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludes.h"

class blockFBase : public virtual blockPortBase
{
public:
    virtual ~blockFBase() = default;
    const uint64_t bob;
    const uint64_t fred;
    // src ports
    // cStuffIf->uThreeCs: An interface for C
    rdy_vld_out< seeSt > cStuffIf;
    // dStuffIf->uBlockF1: An interface for D
    rdy_vld_out< dSt > dSout;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_out< bSizeRegSt > roBsize;

    // dst ports
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_in< dSt > dStuffIf;
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_in< dSt > dSin;


    blockFBase(std::string name, const char * variant) :
        bob(instanceFactory::getParam("blockF", variant, "bob"))
        ,fred(instanceFactory::getParam("blockF", variant, "fred"))
        ,cStuffIf("cStuffIf")
        ,dSout("dSout")
        ,roBsize("roBsize")
        ,dStuffIf("dStuffIf")
        ,dSin("dSin")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dSout->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        dSin->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dSout->setLogging(verbosity);
        roBsize->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
        dSin->setLogging(verbosity);
    };
};
class blockFInverted : public virtual blockPortBase
{
public:
    // src ports
    // cStuffIf->uThreeCs: An interface for C
    rdy_vld_in< seeSt > cStuffIf;
    // dStuffIf->uBlockF1: An interface for D
    rdy_vld_in< dSt > dSout;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_in< bSizeRegSt > roBsize;

    // dst ports
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_out< dSt > dStuffIf;
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_out< dSt > dSin;


    blockFInverted(std::string name) :
        cStuffIf(("cStuffIf"+name).c_str())
        ,dSout(("dSout"+name).c_str())
        ,roBsize(("roBsize"+name).c_str())
        ,dStuffIf(("dStuffIf"+name).c_str())
        ,dSin(("dSin"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dSout->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        dSin->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dSout->setLogging(verbosity);
        roBsize->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
        dSin->setLogging(verbosity);
    };
};
class blockFChannels
{
public:
    // src ports
    // An interface for C
    rdy_vld_channel< seeSt > cStuffIf;
    // An interface for D
    rdy_vld_channel< dSt > dSout;
    // A Read Only register with a structure that has a definition from an included context
    status_channel< bSizeRegSt > roBsize;

    // dst ports
    // An interface for D
    rdy_vld_channel< dSt > dStuffIf;
    // An interface for D
    rdy_vld_channel< dSt > dSin;


    blockFChannels(std::string name, std::string srcName) :
    cStuffIf(("cStuffIf"+name).c_str(), srcName)
    ,dSout(("dSout"+name).c_str(), srcName)
    ,roBsize(("roBsize"+name).c_str(), srcName)
    ,dStuffIf(("dStuffIf"+name).c_str(), srcName)
    ,dSin(("dSin"+name).c_str(), srcName)
    {};
    void bind( blockFBase *a, blockFInverted *b)
    {
        a->cStuffIf( cStuffIf );
        b->cStuffIf( cStuffIf );
        a->dSout( dSout );
        b->dSout( dSout );
        a->roBsize( roBsize );
        b->roBsize( roBsize );
        a->dStuffIf( dStuffIf );
        b->dStuffIf( dStuffIf );
        a->dSin( dSin );
        b->dSin( dSin );
    };
};

// GENERATED_CODE_END

#endif //BLOCKF_BASE_H
