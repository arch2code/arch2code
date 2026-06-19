#ifndef SECONDSUBB_H
#define SECONDSUBB_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=secondSubB
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "secondSubB_base.h"

SC_MODULE(secondSubB), public blockBase, public secondSubBBase
{
private:

public:

    secondSubB(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondSubB() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //SECONDSUBB_H