//

// GENERATED_CODE_PARAM --block=axiSocketSlave_tb --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"

export module axiSocketSlave_tb.base;
import axiSocketSlave_tb;
using namespace axiSocketSlave_tb_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class axiSocketSlave_tbBase : public virtual blockPortBase
{
public:
    virtual ~axiSocketSlave_tbBase() = default;


    axiSocketSlave_tbBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class axiSocketSlave_tbInverted : public virtual blockPortBase
{
public:


    axiSocketSlave_tbInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class axiSocketSlave_tbChannels
{
public:


    axiSocketSlave_tbChannels(std::string name, std::string srcName) 
    {};
    void bind( axiSocketSlave_tbBase *a, axiSocketSlave_tbInverted *b)
    {
    };
};

// GENERATED_CODE_END
