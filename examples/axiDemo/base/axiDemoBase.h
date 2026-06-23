#ifndef AXIDEMO_BASE_H
#define AXIDEMO_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "axi4_stream_channel.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
import axiDemo;
using namespace axiDemo_ns;

class axiDemoBase : public virtual blockPortBase
{
public:
    virtual ~axiDemoBase() = default;


    axiDemoBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class axiDemoInverted : public virtual blockPortBase
{
public:


    axiDemoInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class axiDemoChannels
{
public:


    axiDemoChannels(std::string name, std::string srcName) 
    {};
    void bind( axiDemoBase *a, axiDemoInverted *b)
    {
    };
};


// Force-link function (active modules-mode anchor).
void force_link_axiDemo();
// GENERATED_CODE_END
#endif //AXIDEMO_BASE_H
