// VCS links the SystemC objects twice: once without the HDL, into the
// -syscelab discovery executable that finds the HDL tops sc_main
// instantiates, and once with it into the simv. -ntb_opts uvm-1.2 puts the
// UVM DPI C library (uvm_dpi.cc) into both links, and that library calls the
// SV export m__uvm_report_dpi, which only the simv link defines. This weak
// definition satisfies the discovery link; in the simv link the export VCS
// generates from uvm_pkg is strong and replaces it. The discovery run
// executes no SV, so a call here means the simv lost the real export, and
// the run stops. a2c-uvm.mk compiles this file for VCS UVM builds only.

#include <cstdio>
#include <cstdlib>

extern "C" __attribute__((weak)) void m__uvm_report_dpi(int, const char *, const char *message, int, const char *, int)
{
    std::fprintf(stderr, "uvmVcsElabStub: m__uvm_report_dpi called (%s); the simv was linked without the uvm_pkg DPI export\n",
                 message ? message : "");
    std::abort();
}
