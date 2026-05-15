#ifndef BLOCKC_H
#define BLOCKC_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockCBase.h"

SC_MODULE(blockC), public blockBase, public blockCBase
{
private:

public:

    blockC(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockC() override = default;

    // GENERATED_CODE_END
    // block implementation members
   
};

#endif //BLOCKC_H
