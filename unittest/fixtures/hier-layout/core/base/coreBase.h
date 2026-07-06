#ifndef CORE_BASE_H
#define CORE_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=core
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "push_ack_channel.h"
import core;
using namespace core_ns;

class coreBase : public virtual blockPortBase
{
public:
    virtual ~coreBase() = default;


    coreBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class coreInverted : public virtual blockPortBase
{
public:


    coreInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class coreChannels
{
public:


    coreChannels(std::string name, std::string srcName) 
    {};
    void bind( coreBase *a, coreInverted *b)
    {
    };
};

// GENERATED_CODE_END
#endif //CORE_BASE_H
