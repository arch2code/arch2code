#ifndef TOP_H
#define TOP_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "top_base.h"
#include "apbDecodeIncludes.h"
//contained instances forward class declaration
class cpuBase;
class someRapperBase;

SC_MODULE(top), public blockBase, public topBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<top>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apbReg;

    //instances contained in block
    std::shared_ptr<cpuBase> uCPU;
    std::shared_ptr<someRapperBase> uSomeRapper;

    top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~top() override = default;

    // GENERATED_CODE_END
    // block implementation members
    std::shared_ptr<tracker<simpleString>> pingPong;

};

#endif //TOP_H

