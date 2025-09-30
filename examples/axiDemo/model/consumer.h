#ifndef CONSUMER_H
#define CONSUMER_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "consumer_base.h"
#include "axiDemoIncludes.h"

SC_MODULE(consumer), public blockBase, public consumerBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("consumer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<consumer>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~consumer() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void inAXI0Rd(void);
    void inAXI1Rd(void);
    void inAXI0Wr(void);
    void inAXI1Wr(void);
    void inAXI2Wr(void);
    void inAXI3Wr(void);
};

#endif //CONSUMER_H

