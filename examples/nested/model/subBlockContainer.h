#ifndef SUBBLOCKCONTAINER_H
#define SUBBLOCKCONTAINER_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=subBlockContainer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
import subBlockContainer.base;
#include "rdy_vld_channel.h"
import nested;
using namespace nested_ns;
//contained instances base module imports
import subBlock.base;

SC_MODULE(subBlockContainer), public blockBase, public subBlockContainerBase
{
private:

public:
    // channels
    // Test interface
    rdy_vld_channel< test_st > src;

    //instances contained in block
    std::shared_ptr<subBlockBase> uSubBlock0;
    std::shared_ptr<subBlockBase> uSubBlock1;

    subBlockContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlockContainer() override = default;

    // GENERATED_CODE_END

    // block implementation members
   
};

#endif //SUBBLOCKCONTAINER_H

