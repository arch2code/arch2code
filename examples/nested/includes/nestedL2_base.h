#ifndef NESTEDL2_BASE_H
#define NESTEDL2_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL2
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class nestedL2Base : public virtual blockPortBase
{
public:
    virtual ~nestedL2Base() = default;
    // dst ports
    // External->test: Test interface
    rdy_vld_in< test_st > nested2;


    nestedL2Base(std::string name, const char * variant) :
        nested2("nested2")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested2->setLogging(verbosity);
    };
};
class nestedL2Inverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->test: Test interface
    rdy_vld_out< test_st > nested2;


    nestedL2Inverted(std::string name) :
        nested2(("nested2"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested2->setLogging(verbosity);
    };
};
class nestedL2Channels
{
public:
    // dst ports
    // Test interface
    rdy_vld_channel< test_st > nested2;


    nestedL2Channels(std::string name, std::string srcName) :
    nested2(("nested2"+name).c_str(), srcName)
    {};
    void bind( nestedL2Base *a, nestedL2Inverted *b)
    {
        a->nested2( nested2 );
        b->nested2( nested2 );
    };
};

// GENERATED_CODE_END
#endif //NESTEDL2_BASE_H
