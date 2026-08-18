#ifndef SUBBLOCKCONTAINER_SOCKET_H
#define SUBBLOCKCONTAINER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subBlockContainer
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_subBlockContainer.base;

SC_MODULE(subBlockContainerSocket), public blockBase, public subBlockContainerBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("subBlockContainer_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<subBlockContainerSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    subBlockContainerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlockContainerSocket() override = default;

private:
    void inSocket(void);
    void outSocket(void);

// GENERATED_CODE_END
};

#endif //SUBBLOCKCONTAINER_SOCKET_H
