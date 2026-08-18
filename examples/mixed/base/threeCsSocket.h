#ifndef THREECS_SOCKET_H
#define THREECS_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=threeCs
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import mixed_threeCs.base;

SC_MODULE(threeCsSocket), public blockBase, public threeCsBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("threeCs_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<threeCsSocket>(blockName, variant, bbMode));}, "", "mixed");
        }
    };
    static registerBlock registerBlock_;
public:

    threeCsSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~threeCsSocket() override = default;

private:
    void see0Socket(void);
    void see1Socket(void);
    void see2Socket(void);

// GENERATED_CODE_END
};

#endif //THREECS_SOCKET_H
