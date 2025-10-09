#ifndef PRODUCER_H
#define PRODUCER_H
// copyright the Arch2Code project contributors

#include "systemc.h"


// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "producer_base.h"
#include "nestedTopIncludes.h"

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

    producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producer() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void producerOutRdyVldSizeTransactional1(void);
    void producerOutRdyVldSizeTransactional2(void);
    void producerOutRdyVldSizeTransactional(rdy_vld_out< testDataSt > &outPort, std::string name);
    void producerOutRdyVldSizeNonTransactional(void);

    void producerOutRdyVldTrackerTransactional1(void);
    void producerOutRdyVldTrackerTransactional2(void);
    void producerOutRdyVldTrackerTransactional(rdy_vld_out< testDataSt > &outPort, std::string name);
    void producerOutRdyVldTrackerNonTransactional(void);

    std::list<uint32_t> testSizes; 
    std::shared_ptr<tracker<simpleString>> cmdTracker;
    std::vector<std::shared_ptr<std::vector<uint8_t> > > buffers;
};

#endif //PRODUCER_H

