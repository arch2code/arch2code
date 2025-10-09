#ifndef NESTEDL3_BASE_H
#define NESTEDL3_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL3
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class nestedL3Base : public virtual blockPortBase
{
public:
    virtual ~nestedL3Base() = default;
    // dst ports
    // External->test: Test interface
    rdy_vld_in< test_st > nested3;


    nestedL3Base(std::string name, const char * variant) :
        nested3("nested3")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested3->setLogging(verbosity);
    };
};
class nestedL3Inverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->test: Test interface
    rdy_vld_out< test_st > nested3;


    nestedL3Inverted(std::string name) :
        nested3(("nested3"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested3->setLogging(verbosity);
    };
};
class nestedL3Channels
{
public:
    // dst ports
    // Test interface
    rdy_vld_channel< test_st > nested3;


    nestedL3Channels(std::string name, std::string srcName) :
    nested3(("nested3"+name).c_str(), srcName)
    {};
    void bind( nestedL3Base *a, nestedL3Inverted *b)
    {
        a->nested3( nested3 );
        b->nested3( nested3 );
    };
};

// GENERATED_CODE_END
#endif //NESTEDL3_BASE_H
