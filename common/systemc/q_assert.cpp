#include "logging.h"
#include <boost/stacktrace.hpp>
import a2c.endOfTest;

#include "systemc.h"

namespace {
#ifdef MTI_SYSTEMC
// Questa runs sc_main itself as a thread process, where a2c's sc_main code
// counts as outside any process: wait() is not legal there.
bool inScMain()
{
    sc_process_handle h = sc_get_current_process_handle();
    return h.valid() && std::string_view(h.name()).ends_with("sc_main");
}
#endif

// wait() is only legal from an SC_THREAD/SC_CTHREAD process. Asserts fired
// from sc_module::final(), elaboration, or any other non-process context must
// skip the yields below, otherwise SystemC emits E519 on top of the real
// failure (and the call itself is undefined behavior).
bool inThreadProcess()
{
    if (!sc_is_running()) return false;
    sc_process_handle h = sc_get_current_process_handle();
    if (!h.valid()) return false;
#ifdef MTI_SYSTEMC
    if (inScMain()) return false;
#endif
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
    // After simulation, return so main() reaches exitSummary() and exits with
    // the recorded failure code; an elaboration assert still aborts.
    if (sc_get_status() & (SC_STOPPED | SC_END_OF_SIMULATION)) {
        return;
    }
#ifdef MTI_SYSTEMC
    // The same from Questa's sc_main thread after a time-limited sc_start (an
    // assert in final(), for instance): the status stays SC_PAUSED there, as
    // the sc_stop() above takes effect only once the kernel runs again
    // (questa_sc_main.cpp).
    if (inScMain()) {
        return;
    }
#endif
    sc_assert(false); // should not get here
}
