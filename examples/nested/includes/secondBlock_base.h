#ifndef SECONDBLOCK_BASE_H
#define SECONDBLOCK_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=secondBlock
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class secondBlockBase : public virtual blockPortBase
{
public:
    virtual ~secondBlockBase() = default;
    // src ports
    // beta->uLast: Test interface beta
    rdy_vld_out< test_st > beta;

    // dst ports
    // uFirst->alpha: Test interface alpha
    rdy_vld_in< test_st > primary;


    secondBlockBase(std::string name, const char * variant) :
        beta("beta")
        ,primary("primary")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        beta->setTimed(nsec, mode);
        primary->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        beta->setLogging(verbosity);
        primary->setLogging(verbosity);
    };
};
class secondBlockInverted : public virtual blockPortBase
{
public:
    // src ports
    // beta->uLast: Test interface beta
    rdy_vld_in< test_st > beta;

    // dst ports
    // uFirst->alpha: Test interface alpha
    rdy_vld_out< test_st > primary;


    secondBlockInverted(std::string name) :
        beta(("beta"+name).c_str())
        ,primary(("primary"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        beta->setTimed(nsec, mode);
        primary->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        beta->setLogging(verbosity);
        primary->setLogging(verbosity);
    };
};
class secondBlockChannels
{
public:
    // src ports
    // Test interface beta
    rdy_vld_channel< test_st > beta;

    // dst ports
    // Test interface alpha
    rdy_vld_channel< test_st > primary;


    secondBlockChannels(std::string name, std::string srcName) :
    beta(("beta"+name).c_str(), srcName)
    ,primary(("primary"+name).c_str(), srcName)
    {};
    void bind( secondBlockBase *a, secondBlockInverted *b)
    {
        a->beta( beta );
        b->beta( beta );
        a->primary( primary );
        b->primary( primary );
    };
};

// GENERATED_CODE_END

#endif //SECONDBLOCK_BASE_H
