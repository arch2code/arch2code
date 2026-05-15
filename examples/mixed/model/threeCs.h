#ifndef THREECS_H
#define THREECS_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=threeCs
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "threeCsBase.h"
//contained instances forward class declaration
class blockCBase;

SC_MODULE(threeCs), public blockBase, public threeCsBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<blockCBase> uBlockC0;
    std::shared_ptr<blockCBase> uBlockC1;
    std::shared_ptr<blockCBase> uBlockC2;

    threeCs(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~threeCs() override = default;

    // GENERATED_CODE_END
    // block implementation members
   
};

#endif //THREECS_H
