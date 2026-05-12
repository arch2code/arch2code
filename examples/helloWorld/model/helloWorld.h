#ifndef HELLOWORLD_H
#define HELLOWORLD_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "helloWorldBase.h"
#include "helloWorldTopIncludes.h"
//contained instances forward class declaration
class producerBase;
class consumerBase;

SC_MODULE(helloWorld), public blockBase, public helloWorldBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("helloWorld_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<helloWorld>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    // channels
    // Ready Valid Test interface
    rdy_vld_channel< data_st > test_rdy_vld;
    // Req Ack Test interface
    req_ack_channel< data_st, data_st > test_req_ack;
    // Valid Ack Test interface
    push_ack_channel< data_st > test_push_ack;
    // Ready Ack Test interface
    pop_ack_channel< data_st > test_pop_ack;

    //instances contained in block
    std::shared_ptr<producerBase> uProducer;
    std::shared_ptr<consumerBase> uConsumer;

    helloWorld(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~helloWorld() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //HELLOWORLD_H
