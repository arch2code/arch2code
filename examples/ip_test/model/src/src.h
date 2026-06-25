#ifndef SRC_H
#define SRC_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "srcBase.h"
#include "ipLeafVariantConfig.h"
#include "srcVariantConfig.h"
//contained instances forward class declaration
template<typename Config> class ipLeafBase;

template<typename Config>
SC_MODULE(src), public blockBase, public srcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(src);

    // inherited names usable unqualified (no Config:: / this->)
    using srcBase<Config>::OUT0_DATA_WIDTH;
    using srcBase<Config>::OUT1_DATA_WIDTH;
    using srcBase<Config>::out0;
    using srcBase<Config>::out1;

    //instances contained in block
    std::shared_ptr<ipLeafBase<ipLeafVariantLeaf0Config>> uLeaf;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename srcBase<Config>::srcOut0DataT;
    using typename srcBase<Config>::srcOut1DataT;
    using typename srcBase<Config>::srcOut0St;
    using typename srcBase<Config>::srcOut1St;

    src(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~src() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void driveOut0(void);
    void driveOut1(void);
};

#endif //SRC_H
