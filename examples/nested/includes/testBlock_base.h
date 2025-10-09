#ifndef TESTBLOCK_BASE_H
#define TESTBLOCK_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=testBlock
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class testBlockBase : public virtual blockPortBase
{
public:
    virtual ~testBlockBase() = default;
    // src ports
    // test->uTestBlock1: Test interface
    rdy_vld_out< test_st > loop1src;
    // test->uSubBlockContainer0: Test interface
    rdy_vld_out< test_st > loop2src;

    // dst ports
    // uTestBlock0->test: Test interface
    rdy_vld_in< test_st > loop1dst;
    // uSubBlockContainer0->test: Test interface
    rdy_vld_in< test_st > loop2dst;


    testBlockBase(std::string name, const char * variant) :
        loop1src("loop1src")
        ,loop2src("loop2src")
        ,loop1dst("loop1dst")
        ,loop2dst("loop2dst")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        loop1src->setTimed(nsec, mode);
        loop2src->setTimed(nsec, mode);
        loop1dst->setTimed(nsec, mode);
        loop2dst->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        loop1src->setLogging(verbosity);
        loop2src->setLogging(verbosity);
        loop1dst->setLogging(verbosity);
        loop2dst->setLogging(verbosity);
    };
};
class testBlockInverted : public virtual blockPortBase
{
public:
    // src ports
    // test->uTestBlock1: Test interface
    rdy_vld_in< test_st > loop1src;
    // test->uSubBlockContainer0: Test interface
    rdy_vld_in< test_st > loop2src;

    // dst ports
    // uTestBlock0->test: Test interface
    rdy_vld_out< test_st > loop1dst;
    // uSubBlockContainer0->test: Test interface
    rdy_vld_out< test_st > loop2dst;


    testBlockInverted(std::string name) :
        loop1src(("loop1src"+name).c_str())
        ,loop2src(("loop2src"+name).c_str())
        ,loop1dst(("loop1dst"+name).c_str())
        ,loop2dst(("loop2dst"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        loop1src->setTimed(nsec, mode);
        loop2src->setTimed(nsec, mode);
        loop1dst->setTimed(nsec, mode);
        loop2dst->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        loop1src->setLogging(verbosity);
        loop2src->setLogging(verbosity);
        loop1dst->setLogging(verbosity);
        loop2dst->setLogging(verbosity);
    };
};
class testBlockChannels
{
public:
    // src ports
    // Test interface
    rdy_vld_channel< test_st > loop1src;
    // Test interface
    rdy_vld_channel< test_st > loop2src;

    // dst ports
    // Test interface
    rdy_vld_channel< test_st > loop1dst;
    // Test interface
    rdy_vld_channel< test_st > loop2dst;


    testBlockChannels(std::string name, std::string srcName) :
    loop1src(("loop1src"+name).c_str(), srcName)
    ,loop2src(("loop2src"+name).c_str(), srcName)
    ,loop1dst(("loop1dst"+name).c_str(), srcName)
    ,loop2dst(("loop2dst"+name).c_str(), srcName)
    {};
    void bind( testBlockBase *a, testBlockInverted *b)
    {
        a->loop1src( loop1src );
        b->loop1src( loop1src );
        a->loop2src( loop2src );
        b->loop2src( loop2src );
        a->loop1dst( loop1dst );
        b->loop1dst( loop1dst );
        a->loop2dst( loop2dst );
        b->loop2dst( loop2dst );
    };
};

// GENERATED_CODE_END

#endif //TESTBLOCK_BASE_H
