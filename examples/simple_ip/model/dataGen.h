#ifndef DATAGEN_H
#define DATAGEN_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=dataGen
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import dataGen.base;
#include "push_ack_channel.h"
import simple_ip;
using namespace simple_ip_ns;

SC_MODULE(dataGen), public blockBase, public dataGenBase
{
private:

public:

    dataGen(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dataGen() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void driveOut(void);
};

#endif //DATAGEN_H
