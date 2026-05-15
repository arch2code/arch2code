#ifndef IP_EXTERNAL_H
#define IP_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=ip --variant=variant0
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "ipBase.h"
#include "ipConfig.h"
#include "endOfTest.h"

class ipExternal: public sc_module, public ipInverted<ipVariant0Config> {

    logBlock log_;

public:

    SC_HAS_PROCESS (ipExternal);

    ipExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END

    // Directed stimulus: push one transaction whose payload satisfies the
    // asserts in ip::dataHandler (marker == 1, high data word == 0x2A for
    // IP_DATA_WIDTH > 64), then vote end-of-test. Reaching the line after
    // push() is the functional assertion that the DUT acked.
    void stimulusThread(void);

private:
    endOfTest eot_{true};
};

#endif /* IP_EXTERNAL_H */
