#ifndef DUT_SOCKET_H
#define DUT_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import xif_dut.base;
#include "xifVariantConfig.h"

template<typename Config>
SC_MODULE(dutSocket), public blockBase, public dutBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("dut_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<dutSocket<Config>>(blockName, variant, bbMode));}, variant_, "xif");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(dutSocket);

    dutSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dutSocket() override = default;

private:
    void streamInSocket(void);
    void streamOutSocket(void);

// GENERATED_CODE_END
};

#endif //DUT_SOCKET_H
