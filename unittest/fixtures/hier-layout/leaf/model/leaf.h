#ifndef LEAF_H
#define LEAF_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=leaf
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "leafBase.h"

SC_MODULE(leaf), public blockBase, public leafBase
{
private:

public:

    leaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~leaf() override = default;

    // GENERATED_CODE_END
    // block implementation members

    // Forward every word received on dIn straight out on dOut.
    void forward(void);
};

#endif //LEAF_H
