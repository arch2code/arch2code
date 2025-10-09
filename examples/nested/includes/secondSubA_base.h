#ifndef SECONDSUBA_BASE_H
#define SECONDSUBA_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=secondSubA
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class secondSubABase : public virtual blockPortBase
{
public:
    virtual ~secondSubABase() = default;
    // src ports
    // test->uSecondSubB: Test interface
    rdy_vld_out< test_st > test;

    // dst ports
    // External->alpha: Test interface alpha
    rdy_vld_in< test_st > primary;


    secondSubABase(std::string name, const char * variant) :
        test("test")
        ,primary("primary")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test->setTimed(nsec, mode);
        primary->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test->setLogging(verbosity);
        primary->setLogging(verbosity);
    };
};
class secondSubAInverted : public virtual blockPortBase
{
public:
    // src ports
    // test->uSecondSubB: Test interface
    rdy_vld_in< test_st > test;

    // dst ports
    // External->alpha: Test interface alpha
    rdy_vld_out< test_st > primary;


    secondSubAInverted(std::string name) :
        test(("test"+name).c_str())
        ,primary(("primary"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test->setTimed(nsec, mode);
        primary->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test->setLogging(verbosity);
        primary->setLogging(verbosity);
    };
};
class secondSubAChannels
{
public:
    // src ports
    // Test interface
    rdy_vld_channel< test_st > test;

    // dst ports
    // Test interface alpha
    rdy_vld_channel< test_st > primary;


    secondSubAChannels(std::string name, std::string srcName) :
    test(("test"+name).c_str(), srcName)
    ,primary(("primary"+name).c_str(), srcName)
    {};
    void bind( secondSubABase *a, secondSubAInverted *b)
    {
        a->test( test );
        b->test( test );
        a->primary( primary );
        b->primary( primary );
    };
};

// GENERATED_CODE_END

#endif //SECONDSUBA_BASE_H
