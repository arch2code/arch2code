#ifndef SOMERAPPER_H
#define SOMERAPPER_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "someRapper_base.h"
#include "apbDecodeIncludes.h"
//contained instances forward class declaration
class apbDecodeBase;
class blockABase;
class blockBBase;

SC_MODULE(someRapper), public blockBase, public someRapperBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("someRapper_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<someRapper>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    // channels
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockA;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockB;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<blockABase> uBlockA;
    std::shared_ptr<blockBBase> uBlockB;

    someRapper(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~someRapper() override = default;

// GENERATED_CODE_END
};
#endif //SOMERAPPER_H
