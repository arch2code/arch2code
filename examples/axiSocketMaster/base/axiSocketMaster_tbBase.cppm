//

// GENERATED_CODE_PARAM --block=axiSocketMaster_tb --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"

export module axiSocketMaster_tb.base;
import axiSocketMaster_tb;
using namespace axiSocketMaster_tb_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class axiSocketMaster_tbBase : public virtual blockPortBase
{
public:
    virtual ~axiSocketMaster_tbBase() = default;


    axiSocketMaster_tbBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class axiSocketMaster_tbInverted : public virtual blockPortBase
{
public:


    axiSocketMaster_tbInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class axiSocketMaster_tbChannels
{
public:


    axiSocketMaster_tbChannels(std::string name, std::string srcName) 
    {};
    void bind( axiSocketMaster_tbBase *a, axiSocketMaster_tbInverted *b)
    {
    };
};

// GENERATED_CODE_END
