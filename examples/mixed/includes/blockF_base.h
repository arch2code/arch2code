#ifndef BLOCKF_BASE_H
#define BLOCKF_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
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

    // dst ports
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_in< dSt > dStuffIf;


    blockFBase(std::string name, const char * variant) :
        bob(instanceFactory::getParam("blockF", variant, "bob"))
        ,fred(instanceFactory::getParam("blockF", variant, "fred"))
        ,cStuffIf("cStuffIf")
        ,dStuffIf("dStuffIf")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
    };
};
class blockFInverted : public virtual blockPortBase
{
public:
    // src ports
    // cStuffIf->uThreeCs: An interface for C
    rdy_vld_in< seeSt > cStuffIf;

    // dst ports
    // uBlockD->dStuffIf: An interface for D
    rdy_vld_out< dSt > dStuffIf;


    blockFInverted(std::string name) :
        cStuffIf(("cStuffIf"+name).c_str())
        ,dStuffIf(("dStuffIf"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
    };
};
class blockFChannels
{
public:
    // src ports
    //   cStuffIf
    rdy_vld_channel< seeSt > cStuffIf;

    // dst ports
    //   dStuffIf
    rdy_vld_channel< dSt > dStuffIf;


    blockFChannels(std::string name, std::string srcName) :
    cStuffIf(("cStuffIf"+name).c_str(), srcName)
    ,dStuffIf(("dStuffIf"+name).c_str(), srcName)
    {};
    void bind( blockFBase *a, blockFInverted *b)
    {
        a->cStuffIf( cStuffIf );
        b->cStuffIf( cStuffIf );
        a->dStuffIf( dStuffIf );
        b->dStuffIf( dStuffIf );
    };
};

// GENERATED_CODE_END

#endif //BLOCKF_BASE_H
