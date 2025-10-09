#ifndef NESTEDL5_BASE_H
#define NESTEDL5_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL5
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class nestedL5Base : public virtual blockPortBase
{
public:
    virtual ~nestedL5Base() = default;
    // dst ports
    // External->test: Test interface
    rdy_vld_in< test_st > nested5;


    nestedL5Base(std::string name, const char * variant) :
        nested5("nested5")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested5->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested5->setLogging(verbosity);
    };
};
class nestedL5Inverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->test: Test interface
    rdy_vld_out< test_st > nested5;


    nestedL5Inverted(std::string name) :
        nested5(("nested5"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nested5->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nested5->setLogging(verbosity);
    };
};
class nestedL5Channels
{
public:
    // dst ports
    // Test interface
    rdy_vld_channel< test_st > nested5;


    nestedL5Channels(std::string name, std::string srcName) :
    nested5(("nested5"+name).c_str(), srcName)
    {};
    void bind( nestedL5Base *a, nestedL5Inverted *b)
    {
        a->nested5( nested5 );
        b->nested5( nested5 );
    };
};

// GENERATED_CODE_END
#endif //NESTEDL5_BASE_H
