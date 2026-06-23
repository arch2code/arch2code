#ifndef SIMPLE_H
#define SIMPLE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "simpleBase.h"
import simple;
using namespace simple_ns;
//contained instances forward class declaration
class producerBase;
class consumerBase;

SC_MODULE(simple), public blockBase, public simpleBase
{
private:

public:
    // channels
    // tag interface
    push_ack_channel< tag_st > tag0;
    // tag interface
    push_ack_channel< tag_st > tag1;

    //instances contained in block
    std::shared_ptr<producerBase> u_producer;
    std::shared_ptr<consumerBase> u_consumer;

    simple(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simple() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void doneTest(void);
};

#endif //SIMPLE_H
