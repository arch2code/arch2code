#ifndef SUBBLOCK_H
#define SUBBLOCK_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=subBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
import subBlock.base;
#include "rdy_vld_channel.h"
import nested;
using namespace nested_ns;

SC_MODULE(subBlock), public blockBase, public subBlockBase
{
private:

public:

    subBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlock() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //SUBBLOCK_H