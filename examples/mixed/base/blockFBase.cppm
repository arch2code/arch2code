//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"
#include "status_channel.h"

export module mixed_blockF.base;
import mixed_mixedBlockC;
import mixed;
using namespace mixed_mixedBlockC_ns;
using namespace mixed_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class blockFBase : public virtual blockPortBase
{
public:
    virtual ~blockFBase() = default;
    static constexpr auto bob = Config::bob;
    static constexpr auto fred = Config::fred;
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
    // blockB->reg(rwArr) A Read Write register array
    sc_vector< status_in< dRegSt > > rwArr;


    blockFBase(std::string name, const char * variant) :
        cStuffIf("cStuffIf")
        ,dSout("dSout")
        ,dStuffIf("dStuffIf")
        ,dSin("dSin")
        ,rwD("rwD")
        ,rwArr("rwArr", REGARR_N)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dSout->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        dSin->setTimed(nsec, mode);
        rwD->setTimed(nsec, mode);
        for (auto & p : rwArr) p->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dSout->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
        dSin->setLogging(verbosity);
        rwD->setLogging(verbosity);
        for (auto & p : rwArr) p->setLogging(verbosity);
    };
};
export template<typename Config>
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
    // blockB->reg(rwArr) A Read Write register array
    sc_vector< status_out< dRegSt > > rwArr;


    blockFInverted(std::string name) :
        cStuffIf(("cStuffIf"+name).c_str())
        ,dSout(("dSout"+name).c_str())
        ,dStuffIf(("dStuffIf"+name).c_str())
        ,dSin(("dSin"+name).c_str())
        ,rwD(("rwD"+name).c_str())
        ,rwArr(("rwArr"+name).c_str(), REGARR_N)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cStuffIf->setTimed(nsec, mode);
        dSout->setTimed(nsec, mode);
        dStuffIf->setTimed(nsec, mode);
        dSin->setTimed(nsec, mode);
        rwD->setTimed(nsec, mode);
        for (auto & p : rwArr) p->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cStuffIf->setLogging(verbosity);
        dSout->setLogging(verbosity);
        dStuffIf->setLogging(verbosity);
        dSin->setLogging(verbosity);
        rwD->setLogging(verbosity);
        for (auto & p : rwArr) p->setLogging(verbosity);
    };
};
export template<typename Config>
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
    // A Read Write register array
    sc_vector< status_channel< dRegSt > > rwArr;


    blockFChannels(std::string name, std::string srcName) :
    cStuffIf(("cStuffIf"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,dSout(("dSout"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,dStuffIf(("dStuffIf"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,dSin(("dSin"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,rwD(("rwD"+name).c_str(), srcName)
    ,rwArr(("rwArr"+name).c_str(), REGARR_N, [&](const char * nm, size_t) { return new status_channel< dRegSt >(nm, srcName); })
    {};
    void bind( blockFBase<Config> *a, blockFInverted<Config> *b)
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
        a->rwArr.bind( rwArr );
        b->rwArr.bind( rwArr );
    };
};

// GENERATED_CODE_END
