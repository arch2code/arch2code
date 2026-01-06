#ifndef BLOCKF_BASE_H
#define BLOCKF_BASE_H

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
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

    // dst ports
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_in< dSt > dStuffIf;
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_in< dSt > dSin;
    // blockB->reg(rwD) A Read Write register
    status_in< dRegSt > rwD;


    blockFBase(std::string name, const char * variant) :
        bob(instanceFactory::getParam("blockF", variant, "bob"))
        ,fred(instanceFactory::getParam("blockF", variant, "fred"))
        ,cStuffIf("cStuffIf")
        ,dSout("dSout")
        ,dStuffIf("dStuffIf")
        ,dSin("dSin")
        ,rwD("rwD")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dSout->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        dSin->setTimed(nsec, mode);
        rwD->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dSout->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
        dSin->setLogging(verbosity);
        rwD->setLogging(verbosity);
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

    // dst ports
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_out< dSt > dStuffIf;
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_out< dSt > dSin;
    // blockB->reg(rwD) A Read Write register
    status_out< dRegSt > rwD;


    blockFInverted(std::string name) :
        cStuffIf(("cStuffIf"+name).c_str())
        ,dSout(("dSout"+name).c_str())
        ,dStuffIf(("dStuffIf"+name).c_str())
        ,dSin(("dSin"+name).c_str())
        ,rwD(("rwD"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dSout->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        dSin->setTimed(nsec, mode);
        rwD->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dSout->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
        dSin->setLogging(verbosity);
        rwD->setLogging(verbosity);
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

    // dst ports
    // An interface for D
    rdy_vld_channel< dSt > dStuffIf;
    // An interface for D
    rdy_vld_channel< dSt > dSin;
    // A Read Write register
    status_channel< dRegSt > rwD;


    blockFChannels(std::string name, std::string srcName) :
    cStuffIf(("cStuffIf"+name).c_str(), srcName)
    ,dSout(("dSout"+name).c_str(), srcName)
    ,dStuffIf(("dStuffIf"+name).c_str(), srcName)
    ,dSin(("dSin"+name).c_str(), srcName)
    ,rwD(("rwD"+name).c_str(), srcName)
    {};
    void bind( blockFBase *a, blockFInverted *b)
    {
        a->cStuffIf( cStuffIf );
        b->cStuffIf( cStuffIf );
        a->dSout( dSout );
        b->dSout( dSout );
        a->dStuffIf( dStuffIf );
        b->dStuffIf( dStuffIf );
        a->dSin( dSin );
        b->dSin( dSin );
        a->rwD( rwD );
        b->rwD( rwD );
    };
};

// GENERATED_CODE_END

#endif // BLOCKF_BASE_H
