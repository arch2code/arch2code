//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL1 --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module nested_nestedL1.base;
import nested;
using namespace nested_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class nestedL1Base : public virtual blockPortBase
{
public:
    virtual ~nestedL1Base() = default;
    // dst ports
    // uTestTop->test: Test interface
    rdy_vld_in< test_st > nested1;


    nestedL1Base(std::string name, const char * variant) :
        nested1("nested1")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested1->setLogging(verbosity);
    };
};
export class nestedL1Inverted : public virtual blockPortBase
{
public:
    // dst ports
    // uTestTop->test: Test interface
    rdy_vld_out< test_st > nested1;


    nestedL1Inverted(std::string name) :
        nested1(("nested1"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested1->setLogging(verbosity);
    };
};
export class nestedL1Channels
{
public:
    // dst ports
    // Test interface
    rdy_vld_channel< test_st > nested1;


    nestedL1Channels(std::string name, std::string srcName) :
    nested1(("nested1"+name).c_str(), srcName)
    {};
    void bind( nestedL1Base *a, nestedL1Inverted *b)
    {
        a->nested1( nested1 );
        b->nested1( nested1 );
    };
};

// GENERATED_CODE_END
