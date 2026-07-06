#ifndef GEN_H
#define GEN_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=gen
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "genBase.h"

SC_MODULE(gen), public blockBase, public genBase
{
private:

public:

    gen(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~gen() override = default;

    // GENERATED_CODE_END
    // block implementation members

    // Number of words driven around the gen -> leaf0 -> leaf1 -> gen ring.
    static constexpr int LOOPCOUNT = 64;

    // End-of-test voter: this gen instance casts its vote once it has received
    // and verified the full looped-back sequence.
    endOfTest eot_;

    // Drive the data sequence out of dOut into the leaf pipeline.
    void send(void);
    // Receive the looped-back sequence on dIn, verify it, and vote end-of-test.
    void recv(void);
};

#endif //GEN_H
