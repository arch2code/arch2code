#ifndef CONSUMER_BASE_H
#define CONSUMER_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "axi_read_channel.h"
#include "axi_write_channel.h"
#include "axiDemoIncludes.h"

class consumerBase : public virtual blockPortBase
{
public:
    virtual ~consumerBase() = default;
    // src ports

    // dst ports
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_in< axiAddrSt, axiDataSt > axiRd0;
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_in< axiAddrSt, axiDataSt > axiRd1;
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_in< axiAddrSt, axiDataSt > axiRd2;
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_in< axiAddrSt, axiDataSt > axiRd3;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_in< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_in< axiAddrSt, axiDataSt, axiStrobeSt > axiWr1;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_in< axiAddrSt, axiDataSt, axiStrobeSt > axiWr2;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_in< axiAddrSt, axiDataSt, axiStrobeSt > axiWr3;


    consumerBase(std::string name, const char * variant) :
        axiRd0("axiRd0")
        ,axiRd1("axiRd1")
        ,axiRd2("axiRd2")
        ,axiRd3("axiRd3")
        ,axiWr0("axiWr0")
        ,axiWr1("axiWr1")
        ,axiWr2("axiWr2")
        ,axiWr3("axiWr3")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axiRd0->setTimed(nsec, mode);
        axiRd1->setTimed(nsec, mode);
        axiRd2->setTimed(nsec, mode);
        axiRd3->setTimed(nsec, mode);
        axiWr0->setTimed(nsec, mode);
        axiWr1->setTimed(nsec, mode);
        axiWr2->setTimed(nsec, mode);
        axiWr3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axiRd0->setLogging(verbosity);
        axiRd1->setLogging(verbosity);
        axiRd2->setLogging(verbosity);
        axiRd3->setLogging(verbosity);
        axiWr0->setLogging(verbosity);
        axiWr1->setLogging(verbosity);
        axiWr2->setLogging(verbosity);
        axiWr3->setLogging(verbosity);
    };
};
class consumerInverted : public virtual blockPortBase
{
public:
    // src ports

    // dst ports
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_out< axiAddrSt, axiDataSt > axiRd0;
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_out< axiAddrSt, axiDataSt > axiRd1;
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_out< axiAddrSt, axiDataSt > axiRd2;
    // uProducer->axiRdIf: AXI Read channels; Address and Data
    axi_read_out< axiAddrSt, axiDataSt > axiRd3;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_out< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_out< axiAddrSt, axiDataSt, axiStrobeSt > axiWr1;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_out< axiAddrSt, axiDataSt, axiStrobeSt > axiWr2;
    // uProducer->axiWrIf: AXI Write channels; Address, Data, and Response
    axi_write_out< axiAddrSt, axiDataSt, axiStrobeSt > axiWr3;


    consumerInverted(std::string name) :
        axiRd0(("axiRd0"+name).c_str())
        ,axiRd1(("axiRd1"+name).c_str())
        ,axiRd2(("axiRd2"+name).c_str())
        ,axiRd3(("axiRd3"+name).c_str())
        ,axiWr0(("axiWr0"+name).c_str())
        ,axiWr1(("axiWr1"+name).c_str())
        ,axiWr2(("axiWr2"+name).c_str())
        ,axiWr3(("axiWr3"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axiRd0->setTimed(nsec, mode);
        axiRd1->setTimed(nsec, mode);
        axiRd2->setTimed(nsec, mode);
        axiRd3->setTimed(nsec, mode);
        axiWr0->setTimed(nsec, mode);
        axiWr1->setTimed(nsec, mode);
        axiWr2->setTimed(nsec, mode);
        axiWr3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axiRd0->setLogging(verbosity);
        axiRd1->setLogging(verbosity);
        axiRd2->setLogging(verbosity);
        axiRd3->setLogging(verbosity);
        axiWr0->setLogging(verbosity);
        axiWr1->setLogging(verbosity);
        axiWr2->setLogging(verbosity);
        axiWr3->setLogging(verbosity);
    };
};
class consumerChannels
{
public:
    // src ports

    // dst ports
    //   axiRdIf
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0;
    //   axiRdIf
    axi_read_channel< axiAddrSt, axiDataSt > axiRd1;
    //   axiRdIf
    axi_read_channel< axiAddrSt, axiDataSt > axiRd2;
    //   axiRdIf
    axi_read_channel< axiAddrSt, axiDataSt > axiRd3;
    //   axiWrIf
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;
    //   axiWrIf
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr1;
    //   axiWrIf
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr2;
    //   axiWrIf
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr3;


    consumerChannels(std::string name, std::string srcName) :
    axiRd0(("axiRd0"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiRd1(("axiRd1"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiRd2(("axiRd2"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiRd3(("axiRd3"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiWr0(("axiWr0"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiWr1(("axiWr1"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiWr2(("axiWr2"+name).c_str(), srcName, "api_list_size", 256, "")
    ,axiWr3(("axiWr3"+name).c_str(), srcName, "api_list_size", 256, "")
    {};
    void bind( consumerBase *a, consumerInverted *b)
    {
        a->axiRd0( axiRd0 );
        b->axiRd0( axiRd0 );
        a->axiRd1( axiRd1 );
        b->axiRd1( axiRd1 );
        a->axiRd2( axiRd2 );
        b->axiRd2( axiRd2 );
        a->axiRd3( axiRd3 );
        b->axiRd3( axiRd3 );
        a->axiWr0( axiWr0 );
        b->axiWr0( axiWr0 );
        a->axiWr1( axiWr1 );
        b->axiWr1( axiWr1 );
        a->axiWr2( axiWr2 );
        b->axiWr2( axiWr2 );
        a->axiWr3( axiWr3 );
        b->axiWr3( axiWr3 );
    };
};

// GENERATED_CODE_END

#endif //CONSUMER_BASE_H
