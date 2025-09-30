#ifndef CONSUMER_H
#define CONSUMER_H
// copyright the Arch2Code project contributors

#include "systemc.h"


// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "consumer_base.h"
#include "nestedTopIncludes.h"

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

    void consumerInRdyVldSizeTransactional1(void);
    void consumerInRdyVldSizeTransactional2(void);
    void consumerInRdyVldSizeTransactional(rdy_vld_in< testDataSt > &inPort, std::string name_);
    void consumerInRdyVldSizeNonTransactional(void);

    void consumerInRdyVldTrackerTransactional1(void);
    void consumerInRdyVldTrackerTransactional2(void);
    void consumerInRdyVldTrackerTransactional(rdy_vld_in< testDataSt > &inPort, std::string name_);
    void consumerInRdyVldTrackerNonTransactional(void);
    std::list<uint32_t> testSizes; 
    std::shared_ptr<tracker<simpleString>> cmdTracker;

};

#endif //CONSUMER_H

