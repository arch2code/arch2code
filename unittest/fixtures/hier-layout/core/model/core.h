#ifndef CORE_H
#define CORE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=core
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "coreBase.h"
import core;
using namespace core_ns;
//contained instances forward class declaration
class genBase;
class leafBase;

SC_MODULE(core), public blockBase, public coreBase
{
private:

public:
    // channels
    // data interface
    push_ack_channel< dat_st > dOut_0;
    // data interface
    push_ack_channel< dat_st > dOut_1;
    // data interface
    push_ack_channel< dat_st > dOut_2;

    //instances contained in block
    std::shared_ptr<genBase> u_gen;
    std::shared_ptr<leafBase> u_leaf0;
    std::shared_ptr<leafBase> u_leaf1;

    core(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~core() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //CORE_H
