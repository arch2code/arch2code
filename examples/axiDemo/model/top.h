#ifndef TOP_H
#define TOP_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "top_base.h"
#include "axiDemoIncludes.h"
//contained instances forward class declaration
class producerBase;
class consumerBase;

SC_MODULE(top), public blockBase, public topBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<top>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    // channels
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0;
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd1;
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd2;
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd3;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr1;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr2;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr3;

    //instances contained in block
    std::shared_ptr<producerBase> uProducer;
    std::shared_ptr<consumerBase> uConsumer;

    top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~top() override = default;

    // GENERATED_CODE_END
    // block implementation members


};

#endif //TOP_H

