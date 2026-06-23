#ifndef SIMPLE_BASE_H
#define SIMPLE_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "push_ack_channel.h"
import simple;
using namespace simple_ns;

class simpleBase : public virtual blockPortBase
{
public:
    virtual ~simpleBase() = default;


    simpleBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class simpleInverted : public virtual blockPortBase
{
public:


    simpleInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class simpleChannels
{
public:


    simpleChannels(std::string name, std::string srcName) 
    {};
    void bind( simpleBase *a, simpleInverted *b)
    {
    };
};

// GENERATED_CODE_END
#endif //SIMPLE_BASE_H
