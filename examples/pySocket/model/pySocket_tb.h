#ifndef PYSOCKET_TB_H
#define PYSOCKET_TB_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=pySocket_tb
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "pySocket_tbBase.h"
#include "pySocketIncludes.h"
//contained instances forward class declaration
class pySocketBase;
class dutBase;

SC_MODULE(pySocket_tb), public blockBase, public pySocket_tbBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("pySocket_tb_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<pySocket_tb>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    // channels
    // Req Ack Test interface
    req_ack_channel< p2s_message_st, p2s_response_st > test_req_ack;
    // Req Ack Test2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > test2Python_req_ack;
    // Req Ack Dut2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > dut2Python_req_ack;

    //instances contained in block
    std::shared_ptr<pySocketBase> u_pySocket;
    std::shared_ptr<dutBase> u_dut;

    pySocket_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocket_tb() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //PYSOCKET_TB_H
