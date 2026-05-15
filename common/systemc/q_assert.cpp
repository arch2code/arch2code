#include "logging.h"
#include <boost/stacktrace.hpp>
#include "endOfTest.h"

#include "systemc.h"

namespace {
// wait() is only legal from an SC_THREAD/SC_CTHREAD process. Asserts fired
// from sc_module::final(), elaboration, or any other non-process context must
// skip the yields below, otherwise SystemC emits E519 on top of the real
// failure (and the call itself is undefined behavior).
bool inThreadProcess()
{
    if (!sc_is_running()) return false;
    sc_process_handle h = sc_get_current_process_handle();
    if (!h.valid()) return false;
    sc_curr_proc_kind k = h.proc_kind();
    return k == SC_THREAD_PROC_ || k == SC_CTHREAD_PROC_;
}
} // namespace

void q_assert_body(bool dump, const char * file, int line, std::string ctx, std::string msg, std::string ctx_msg)
{
    static std::string firstAssert;
    static std::string firstFile(file);
    static int firstLine(line);
    {
        std::stringstream ss;
        ss << "[Q_ASSERT]";
        if(ctx != "") ss << "[" << ctx << "]";
        ss << " " << msg << " (" << file << ":" << line << ")";
        firstAssert = ss.str();
        std::cout << firstAssert << std::endl;
        if(ctx_msg != "") std::cout << " Context Message: " << ctx_msg << std::endl;
        std::cout << boost::stacktrace::stacktrace() << std::endl;
        logging::GetInstance().statusPrint();
        if (dump) {
            logging::GetInstance().trackerDump();
        }
        #ifndef RUNNING_IN_DEBUGGER
        if (inThreadProcess()) {
            wait(10, SC_NS);
        }
        #endif
        errorCode::fail(firstAssert, 1);
        endOfTestState::GetInstance().forceEndOfTest();
    }
    REAL_ASSERT; // Trigger to preserve callstack if RUNNING_IN_DEBUGGER, otherwise continue to sc_stop()
    if (inThreadProcess()) {
        wait(SC_ZERO_TIME);
    }
    if (sc_is_running()) {
        sc_stop();
    }
    if (inThreadProcess()) {
        wait(SC_ZERO_TIME);
    }
    sc_assert(false); // should not get here
}
