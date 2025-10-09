#ifndef TESTCONTAINER_BASE_H
#define TESTCONTAINER_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=testContainer
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class testContainerBase : public virtual blockPortBase
{
public:
    virtual ~testContainerBase() = default;
    // src ports
    // test->uNestedL1: Test interface
    rdy_vld_out< test_st > test;


    testContainerBase(std::string name, const char * variant) :
        test("test")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test->setLogging(verbosity);
    };
};
class testContainerInverted : public virtual blockPortBase
{
public:
    // src ports
    // test->uNestedL1: Test interface
    rdy_vld_in< test_st > test;


    testContainerInverted(std::string name) :
        test(("test"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test->setLogging(verbosity);
    };
};
class testContainerChannels
{
public:
    // src ports
    // Test interface
    rdy_vld_channel< test_st > test;


    testContainerChannels(std::string name, std::string srcName) :
    test(("test"+name).c_str(), srcName)
    {};
    void bind( testContainerBase *a, testContainerInverted *b)
    {
        a->test( test );
        b->test( test );
    };
};

// GENERATED_CODE_END

#endif //TESTCONTAINER_BASE_H
