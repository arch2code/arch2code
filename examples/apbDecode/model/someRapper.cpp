//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "someRapper.h"
#include "apbDecode_base.h"
#include "blockA_base.h"
#include "blockB_base.h"
SC_HAS_PROCESS(someRapper);

someRapper::registerBlock someRapper::registerBlock_; //register the block with the factory

someRapper::someRapper(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("someRapper", name(), bbMode)
        ,someRapperBase(name(), variant)
        ,apb_uBlockA("blockA_apb_uBlockA", "apbDecode")
        ,apb_uBlockB("blockB_apb_uBlockB", "apbDecode")
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>( instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "")))
        ,uBlockA(std::dynamic_pointer_cast<blockABase>( instanceFactory::createInstance(name(), "uBlockA", "blockA", "")))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>( instanceFactory::createInstance(name(), "uBlockB", "blockB", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->apbReg(apbReg);
// instance to instance connections via channel
    uAPBDecode->apb_uBlockA(apb_uBlockA);
    uBlockA->apbReg(apb_uBlockA);
    uAPBDecode->apb_uBlockB(apb_uBlockB);
    uBlockB->apbReg(apb_uBlockB);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

