//

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "dut.h"
SC_HAS_PROCESS(dut);

dut::registerBlock dut::registerBlock_; //register the block with the factory

dut::dut(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("dut", name(), bbMode)
        ,dutBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(dutListener);
};

void dut::dutListener(void)
{
    log_.logPrint(std::format("started dutListener"), LOG_IMPORTANT );
    while (true)
    {
        p2s_message_st message;
        p2s_response_st response;
        test_req_ack->reqReceive(message);
        log_.logPrint(std::format("received message: {}", message.param1), LOG_IMPORTANT );
        response.response = message.param1 + message.param2;
        test_req_ack->ack(response);
    }
}
