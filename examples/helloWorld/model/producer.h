#ifndef PRODUCER_H
#define PRODUCER_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "producer_base.h"
#include "helloWorldTopIncludes.h"

SC_MODULE(producer), public blockBase, public producerBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("producer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<producer>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producer() override = default;

    // GENERATED_CODE_END

    // block implementation members
    void producerOutRdyVld(void);
    void producerOutPushAck(void);
    void producerOutReqAck(void);
    void producerOutPopAck(void);
};

#endif //PRODUCER_H

