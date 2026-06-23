#ifndef NESTED_H
#define NESTED_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedBase.h"
import nested;
using namespace nested_ns;
//contained instances forward class declaration
class testContainerBase;
class nestedL1Base;

SC_MODULE(nested), public blockBase, public nestedBase
{
private:

public:
    // channels
    // Test interface
    rdy_vld_channel< test_st > test;

    //instances contained in block
    std::shared_ptr<testContainerBase> uTestTop;
    std::shared_ptr<nestedL1Base> uNestedL1;

    nested(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nested() override = default;

    // GENERATED_CODE_END
    // block implementation members

    // Bridges testController completion to the end-of-test voting mechanism.
    void doneTest(void);

};

#endif //NESTED_H
