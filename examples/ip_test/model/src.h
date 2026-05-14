#ifndef SRC_H
#define SRC_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "srcBase.h"
#include "ipLeafConfig.h"
#include "srcConfig.h"
//contained instances forward class declaration
template<typename Config> class ipLeafBase;

template<typename Config>
SC_MODULE(src), public blockBase, public srcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(src);

    //instances contained in block
    std::shared_ptr<ipLeafBase<ipLeafVariantLeaf0Config>> uLeaf;

    src(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~src() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void driveOut0(void);
    void driveOut1(void);
};

#endif //SRC_H
