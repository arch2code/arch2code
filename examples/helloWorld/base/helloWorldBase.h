#ifndef HELLOWORLD_BASE_H
#define HELLOWORLD_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "helloWorldTopIncludes.h"

class helloWorldBase : public virtual blockPortBase
{
public:
    virtual ~helloWorldBase() = default;


    helloWorldBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class helloWorldInverted : public virtual blockPortBase
{
public:


    helloWorldInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class helloWorldChannels
{
public:


    helloWorldChannels(std::string name, std::string srcName) 
    {};
    void bind( helloWorldBase *a, helloWorldInverted *b)
    {
    };
};

// GENERATED_CODE_END
#endif //HELLOWORLD_BASE_H
