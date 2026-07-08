
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "testController.h"

// GENERATED_CODE_PARAM --block=firstBlock
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "firstBlock.h"
SC_HAS_PROCESS(firstBlock);

// === Block factory registration (firstBlock) ===
void register_firstBlock_variants() {
    instanceFactory::registerBlock("firstBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<firstBlock>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _firstBlock_registered = (register_firstBlock_variants(), 0);
} // namespace
// === End block factory registration ===

firstBlock::firstBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("firstBlock", name(), bbMode)
        ,firstBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(producer);
    SC_THREAD(consumer);
}

// this module just takes data from the input and sends it to the output

void firstBlock::producer(void)
{
    std::string test_name = "test2";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    test_st data;
    data.a = 0;
    wait(SC_ZERO_TIME);
    for(int i=0; i<10; i++) {
        data.a = i;
        std::cout << __func__ << " write test " << data.a << endl;
        primary->write(data);
    }
    controller.test_complete(test_name);
};

void firstBlock::consumer(void)
{
    std::string test_name = "test2";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    test_st data;
    data.a=0;
    while (data.a < 9)
    {
        response->read(data);
        std::cout << __func__ << " read test " << data.a << endl;
    }
    controller.test_complete(test_name);
}