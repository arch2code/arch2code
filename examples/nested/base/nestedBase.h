#ifndef NESTED_BASE_H
#define NESTED_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
import nested;
using namespace nested_ns;

class nestedBase : public virtual blockPortBase
{
public:
    virtual ~nestedBase() = default;


    nestedBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class nestedInverted : public virtual blockPortBase
{
public:


    nestedInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class nestedChannels
{
public:


    nestedChannels(std::string name, std::string srcName) 
    {};
    void bind( nestedBase *a, nestedInverted *b)
    {
    };
};


// Force-link function (active modules-mode anchor).
void force_link_nested();
// GENERATED_CODE_END
#endif //NESTED_BASE_H
