#ifndef NESTEDL4_BASE_H
#define NESTEDL4_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL4
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class nestedL4Base : public virtual blockPortBase
{
public:
    virtual ~nestedL4Base() = default;
    // dst ports
    // External->test: Test interface
    rdy_vld_in< test_st > nested4;


    nestedL4Base(std::string name, const char * variant) :
        nested4("nested4")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested4->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested4->setLogging(verbosity);
    };
};
class nestedL4Inverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->test: Test interface
    rdy_vld_out< test_st > nested4;


    nestedL4Inverted(std::string name) :
        nested4(("nested4"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested4->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested4->setLogging(verbosity);
    };
};
class nestedL4Channels
{
public:
    // dst ports
    // Test interface
    rdy_vld_channel< test_st > nested4;


    nestedL4Channels(std::string name, std::string srcName) :
    nested4(("nested4"+name).c_str(), srcName)
    {};
    void bind( nestedL4Base *a, nestedL4Inverted *b)
    {
        a->nested4( nested4 );
        b->nested4( nested4 );
    };
};

// GENERATED_CODE_END
#endif //NESTEDL4_BASE_H
