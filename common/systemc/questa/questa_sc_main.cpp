// Questa's sc_main, compiled by sccom (a2c-questa.mk). sccom -link builds the
// SystemC library only around an object sccom compiled itself, and vopt and
// vsim look for sc_main as a design unit of that library, so this stub is the
// sc_main they see. It calls a2c's sc_main, which main.cpp compiles as
// a2c_sc_main under QUESTA, and hands its result to vsim as the exit code on
// every return path: returning from sc_main would leave vsim to destroy
// objects the simulation still owns. vopt runs sc_main only to elaborate.
// A run that ends at --scTimeLimit leaves the simulation paused, and vsim
// then crashes (SIGSEGV, exit code 211) destroying a2c's static instance map
// as it quits, so the stub first lets the kernel stop.
#include <systemc.h>
#include <iostream>

extern "C" int a2c_sc_main(int argc, char* argv[]);

int sc_main(int argc, char* argv[])
{
    int rc = a2c_sc_main(argc, argv);
    if (!mti_IsVoptMode()) {
        if (sc_get_status() == SC_PAUSED) {
            sc_stop();
            sc_start(SC_ZERO_TIME);
        }
        std::cout.flush();
        mti_QuitWithErrorCode(__FILE__, __LINE__, rc);
    }
    return rc;
}

// The definitions systemc.h in this directory declares extern.
#define A2C_QUESTA_PTRARRAY(T) template class ptrarray<T>;
#include "a2c_questa_ptrarray.def"
#undef A2C_QUESTA_PTRARRAY
