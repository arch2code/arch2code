#ifndef FIRSTBLOCK_H
#define FIRSTBLOCK_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=firstBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "firstBlock_base.h"

SC_MODULE(firstBlock), public blockBase, public firstBlockBase
{
private:

public:

    firstBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~firstBlock() override = default;

// GENERATED_CODE_END

    void producer(void);
    void consumer(void);

    // block implementation members
};


#endif  //SUBBLOCK_H