#ifndef TOP_H
#define TOP_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "top_base.h"
#include "helloWorldTopIncludes.h"
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
    //   test_rdy_vld
    rdy_vld_channel< data_st > test_rdy_vld;
    //   test_req_ack
    req_ack_channel< data_st, data_st > test_req_ack;
    //   test_push_ack
    push_ack_channel< data_st > test_push_ack;
    //   test_pop_ack
    pop_ack_channel< data_st > test_pop_ack;

    //instances contained in block
    std::shared_ptr<producerBase> uProducer;
    std::shared_ptr<consumerBase> uConsumer;

    top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~top() override = default;

    // GENERATED_CODE_END
    // block implementation members
    std::shared_ptr<tracker<simpleString>> pingPong;

};

#endif //TOP_H

