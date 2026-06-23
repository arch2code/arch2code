#ifndef SECONDSUBA_H
#define SECONDSUBA_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=secondSubA
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "secondSubABase.h"

SC_MODULE(secondSubA), public blockBase, public secondSubABase
{
private:

public:

    secondSubA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondSubA() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //SECONDSUBA_H