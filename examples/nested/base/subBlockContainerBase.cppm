//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subBlockContainer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module nested_subBlockContainer.base;
import nested;
using namespace nested_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class subBlockContainerBase : public virtual blockPortBase
{
public:
    virtual ~subBlockContainerBase() = default;
    // src ports
    // test->uTestBlock0: Test interface
    rdy_vld_out< test_st > out;

    // dst ports
    // uTestBlock0->test: Test interface
    rdy_vld_in< test_st > in;


    subBlockContainerBase(std::string name, const char * variant) :
        out("out")
        ,in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
};
export class subBlockContainerInverted : public virtual blockPortBase
{
public:
    // src ports
    // test->uTestBlock0: Test interface
    rdy_vld_in< test_st > out;

    // dst ports
    // uTestBlock0->test: Test interface
    rdy_vld_out< test_st > in;


    subBlockContainerInverted(std::string name) :
        out(("out"+name).c_str())
        ,in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
};
export class subBlockContainerChannels
{
public:
    // src ports
    // Test interface
    rdy_vld_channel< test_st > out;

    // dst ports
    // Test interface
    rdy_vld_channel< test_st > in;


    subBlockContainerChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,in(("in"+name).c_str(), srcName)
    {};
    void bind( subBlockContainerBase *a, subBlockContainerInverted *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
