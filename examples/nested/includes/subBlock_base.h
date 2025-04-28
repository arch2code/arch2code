#ifndef SUBBLOCK_BASE_H
#define SUBBLOCK_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=subBlock
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class subBlockBase : public virtual blockPortBase
{
public:
    virtual ~subBlockBase() = default;
    // src ports
    // test->External: Test interface
    rdy_vld_out< test_st > src;

    // dst ports
    // External->test: Test interface
    rdy_vld_in< test_st > dst;


    subBlockBase(std::string name, const char * variant) :
        src("src")
        ,dst("dst")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        src->setTimed(nsec, mode);
        dst->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        src->setLogging(verbosity);
        dst->setLogging(verbosity);
    };
};
class subBlockInverted : public virtual blockPortBase
{
public:
    // src ports
    // test->External: Test interface
    rdy_vld_in< test_st > src;

    // dst ports
    // External->test: Test interface
    rdy_vld_out< test_st > dst;


    subBlockInverted(std::string name) :
        src(("src"+name).c_str())
        ,dst(("dst"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        src->setTimed(nsec, mode);
        dst->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        src->setLogging(verbosity);
        dst->setLogging(verbosity);
    };
};
class subBlockChannels
{
public:
    // src ports
    //   test
    rdy_vld_channel< test_st > src;

    // dst ports
    //   test
    rdy_vld_channel< test_st > dst;


    subBlockChannels(std::string name, std::string srcName) :
    src(("src"+name).c_str(), srcName)
    ,dst(("dst"+name).c_str(), srcName)
    {};
    void bind( subBlockBase *a, subBlockInverted *b)
    {
        a->src( src );
        b->src( src );
        a->dst( dst );
        b->dst( dst );
    };
};

// GENERATED_CODE_END

#endif //SUBBLOCK_BASE_H
