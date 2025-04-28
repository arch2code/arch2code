#ifndef SECONDSUBB_BASE_H
#define SECONDSUBB_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=secondSubB
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class secondSubBBase : public virtual blockPortBase
{
public:
    virtual ~secondSubBBase() = default;
    // src ports
    // beta->External: Test interface beta
    rdy_vld_out< test_st > beta;

    // dst ports
    // uSecondSubA->test: Test interface
    rdy_vld_in< test_st > test;


    secondSubBBase(std::string name, const char * variant) :
        beta("beta")
        ,test("test")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        beta->setTimed(nsec, mode);
        test->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        beta->setLogging(verbosity);
        test->setLogging(verbosity);
    };
};
class secondSubBInverted : public virtual blockPortBase
{
public:
    // src ports
    // beta->External: Test interface beta
    rdy_vld_in< test_st > beta;

    // dst ports
    // uSecondSubA->test: Test interface
    rdy_vld_out< test_st > test;


    secondSubBInverted(std::string name) :
        beta(("beta"+name).c_str())
        ,test(("test"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        beta->setTimed(nsec, mode);
        test->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        beta->setLogging(verbosity);
        test->setLogging(verbosity);
    };
};
class secondSubBChannels
{
public:
    // src ports
    //   beta
    rdy_vld_channel< test_st > beta;

    // dst ports
    //   test
    rdy_vld_channel< test_st > test;


    secondSubBChannels(std::string name, std::string srcName) :
    beta(("beta"+name).c_str(), srcName)
    ,test(("test"+name).c_str(), srcName)
    {};
    void bind( secondSubBBase *a, secondSubBInverted *b)
    {
        a->beta( beta );
        b->beta( beta );
        a->test( test );
        b->test( test );
    };
};

// GENERATED_CODE_END

#endif //SECONDSUBB_BASE_H
