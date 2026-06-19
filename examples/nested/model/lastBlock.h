#ifndef LASTBLOCK_H
#define LASTBLOCK_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=lastBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "lastBlock_base.h"

SC_MODULE(lastBlock), public blockBase, public lastBlockBase
{
private:

public:

    lastBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~lastBlock() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //LASTBLOCK_H