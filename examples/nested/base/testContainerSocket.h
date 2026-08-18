#ifndef TESTCONTAINER_SOCKET_H
#define TESTCONTAINER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=testContainer
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_testContainer.base;

SC_MODULE(testContainerSocket), public blockBase, public testContainerBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("testContainer_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<testContainerSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    testContainerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~testContainerSocket() override = default;

private:
    void testSocket(void);

// GENERATED_CODE_END
};

#endif //TESTCONTAINER_SOCKET_H
