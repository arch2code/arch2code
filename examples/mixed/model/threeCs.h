#ifndef THREECS_H
#define THREECS_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "mixedIncludes.h"

// GENERATED_CODE_PARAM --block=threeCs
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "threeCs_base.h"
#include "mixedBlockCIncludes.h"
//contained instances forward class declaration
class blockCBase;

SC_MODULE(threeCs), public blockBase, public threeCsBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("threeCs_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<threeCs>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    //instances contained in block
    std::shared_ptr<blockCBase> uBlockC0;
    std::shared_ptr<blockCBase> uBlockC1;
    std::shared_ptr<blockCBase> uBlockC2;

    threeCs(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~threeCs() override = default;

    // GENERATED_CODE_END
    // block implementation members
   
};

#endif //THREECS_H
