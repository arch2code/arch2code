#ifndef THREECS_BASE_H
#define THREECS_BASE_H

// GENERATED_CODE_PARAM --block=threeCs
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "mixedBlockCIncludes.h"

class threeCsBase : public virtual blockPortBase
{
public:
    virtual ~threeCsBase() = default;
    // dst ports
    // uBlockD->cStuffIf: An interface for C
    rdy_vld_in< seeSt > see0;
    // uBlockF0->cStuffIf: An interface for C
    rdy_vld_in< seeSt > see1;
    // uBlockF1->cStuffIf: An interface for C
    rdy_vld_in< seeSt > see2;


    threeCsBase(std::string name, const char * variant) :
        see0("see0")
        ,see1("see1")
        ,see2("see2")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        see0->setTimed(nsec, mode);
        see1->setTimed(nsec, mode);
        see2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        see0->setLogging(verbosity);
        see1->setLogging(verbosity);
        see2->setLogging(verbosity);
    };
};
class threeCsInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uBlockD->cStuffIf: An interface for C
    rdy_vld_out< seeSt > see0;
    // uBlockF0->cStuffIf: An interface for C
    rdy_vld_out< seeSt > see1;
    // uBlockF1->cStuffIf: An interface for C
    rdy_vld_out< seeSt > see2;


    threeCsInverted(std::string name) :
        see0(("see0"+name).c_str())
        ,see1(("see1"+name).c_str())
        ,see2(("see2"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        see0->setTimed(nsec, mode);
        see1->setTimed(nsec, mode);
        see2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        see0->setLogging(verbosity);
        see1->setLogging(verbosity);
        see2->setLogging(verbosity);
    };
};
class threeCsChannels
{
public:
    // dst ports
    // An interface for C
    rdy_vld_channel< seeSt > see0;
    // An interface for C
    rdy_vld_channel< seeSt > see1;
    // An interface for C
    rdy_vld_channel< seeSt > see2;


    threeCsChannels(std::string name, std::string srcName) :
    see0(("see0"+name).c_str(), srcName)
    ,see1(("see1"+name).c_str(), srcName)
    ,see2(("see2"+name).c_str(), srcName)
    {};
    void bind( threeCsBase *a, threeCsInverted *b)
    {
        a->see0( see0 );
        b->see0( see0 );
        a->see1( see1 );
        b->see1( see1 );
        a->see2( see2 );
        b->see2( see2 );
    };
};

// GENERATED_CODE_END

#endif // THREECS_BASE_H
