//

// GENERATED_CODE_PARAM --block=producer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"

export module axiSocketSlave_producer.base;
import axiSocketSlave_tb;
using namespace axiSocketSlave_tb_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class producerBase : public virtual blockPortBase
{
public:
    virtual ~producerBase() = default;
    // src ports
    // axiRdIf->u_axiSocket: AXI Read channels; Address and Data
    axi_read_out< axiAddrSt, axiDataSt > axiRd0;
    // axiWrIf->u_axiSocket: AXI Write channels; Address, Data, and Response
    axi_write_out< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;


    producerBase(std::string name, const char * variant) :
        axiRd0("axiRd0")
        ,axiWr0("axiWr0")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axiRd0->setTimed(nsec, mode);
        axiWr0->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axiRd0->setLogging(verbosity);
        axiWr0->setLogging(verbosity);
    };
};
export class producerInverted : public virtual blockPortBase
{
public:
    // src ports
    // axiRdIf->u_axiSocket: AXI Read channels; Address and Data
    axi_read_in< axiAddrSt, axiDataSt > axiRd0;
    // axiWrIf->u_axiSocket: AXI Write channels; Address, Data, and Response
    axi_write_in< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;


    producerInverted(std::string name) :
        axiRd0(("axiRd0"+name).c_str())
        ,axiWr0(("axiWr0"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axiRd0->setTimed(nsec, mode);
        axiWr0->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axiRd0->setLogging(verbosity);
        axiWr0->setLogging(verbosity);
    };
};
export class producerChannels
{
public:
    // src ports
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;


    producerChannels(std::string name, std::string srcName) :
    axiRd0(("axiRd0"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiWr0(("axiWr0"+name).c_str(), srcName, "api_list_size", 256, "")
    {};
    void bind( producerBase *a, producerInverted *b)
    {
        a->axiRd0( axiRd0 );
        b->axiRd0( axiRd0 );
        a->axiWr0( axiWr0 );
        b->axiWr0( axiWr0 );
    };
};

// GENERATED_CODE_END
