#ifndef NESTEDL6_BASE_H
#define NESTEDL6_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL6
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class nestedL6Base : public virtual blockPortBase
{
public:
    virtual ~nestedL6Base() = default;
    // dst ports
    // External->test: Test interface
    rdy_vld_in< test_st > nested6;


    nestedL6Base(std::string name, const char * variant) :
        nested6("nested6")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested6->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested6->setLogging(verbosity);
    };
};
class nestedL6Inverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->test: Test interface
    rdy_vld_out< test_st > nested6;


    nestedL6Inverted(std::string name) :
        nested6(("nested6"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested6->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested6->setLogging(verbosity);
    };
};
class nestedL6Channels
{
public:
    // dst ports
    // Test interface
    rdy_vld_channel< test_st > nested6;


    nestedL6Channels(std::string name, std::string srcName) :
    nested6(("nested6"+name).c_str(), srcName)
    {};
    void bind( nestedL6Base *a, nestedL6Inverted *b)
    {
        a->nested6( nested6 );
        b->nested6( nested6 );
    };
};

// GENERATED_CODE_END
#endif //NESTEDL6_BASE_H
