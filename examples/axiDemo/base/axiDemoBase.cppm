//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=axiDemo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi4_stream_channel.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"

export module axiDemo.base;
import axiDemo;
using namespace axiDemo_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class axiDemoBase : public virtual blockPortBase
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
export class axiDemoInverted : public virtual blockPortBase
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
export class axiDemoChannels
{
public:


    axiDemoChannels(std::string name, std::string srcName) 
    {};
    void bind( axiDemoBase *a, axiDemoInverted *b)
    {
    };
};

// GENERATED_CODE_END
