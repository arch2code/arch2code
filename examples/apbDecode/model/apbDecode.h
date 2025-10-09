#ifndef APBDECODE_H
#define APBDECODE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "apbBusDecode.h"

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "apbDecode_base.h"
#include "apbDecodeIncludes.h"
#include "apbBusDecode.h"

SC_MODULE(apbDecode), public blockBase, public apbDecodeBase
{
private:
    void routerDecode(void);
    abpBusDecode< apbAddrSt, apbDataSt > decoder;

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("apbDecode_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<apbDecode>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    apbDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~apbDecode() override = default;

    // GENERATED_CODE_END

};

#endif //APBDECODE_H
