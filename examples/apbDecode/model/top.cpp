// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <memory>
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "top.h"
#include "cpu_base.h"
#include "someRapper_base.h"
SC_HAS_PROCESS(top);

top::registerBlock top::registerBlock_; //register the block with the factory

top::top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("top", name(), bbMode)
        ,topBase(name(), variant)
        ,apbReg("someRapper_apbReg", "cpu")
        ,uCPU(std::dynamic_pointer_cast<cpuBase>( instanceFactory::createInstance(name(), "uCPU", "cpu", "")))
        ,uSomeRapper(std::dynamic_pointer_cast<someRapperBase>( instanceFactory::createInstance(name(), "uSomeRapper", "someRapper", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// instance to instance connections via channel
    uCPU->apbReg(apbReg);
    uSomeRapper->apbReg(apbReg);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    //auto baseInstance = instanceFactory::createInstance("uProducer");
    //uProducer2 = (producer *) baseInstance.get();
}
