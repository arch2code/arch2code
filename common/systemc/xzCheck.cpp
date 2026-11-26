#include <string>

#include "logging.h"

// DPI import of the <type>_xcheck modules (common/systemVerilog/a2c_xcheck.svh),
// called once per checker instance on its first X or Z. Verilated wrappers do
// not instantiate the checkers, so Verilator builds link it without calling it.
extern "C" void a2c_xz_fail(const char* path, const char* signal)
{
    errorCode::fail(std::string("A2C_XZ ") + path + ": " + signal + " is X or Z");
}
