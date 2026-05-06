#ifndef SRC_H
#define SRC_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "srcBase.h"
#include "ipConfig.h"
import ip;
using namespace ip_ns;

template<typename Config>
SC_MODULE(src), public blockBase, public srcBase<Config>
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("src_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<src<ipDefaultConfig>>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(src);


    src(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~src() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void driveOut0(void);
    void driveOut1(void);
};

#endif //SRC_H
