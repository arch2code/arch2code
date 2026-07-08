//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=secondSubA --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module secondSubA.base;
import nested;
using namespace nested_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class secondSubABase : public virtual blockPortBase
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
export class secondSubAInverted : public virtual blockPortBase
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
export class secondSubAChannels
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
