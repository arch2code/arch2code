#include "logging.h"
#include <boost/stacktrace.hpp>
#include "endOfTest.h"

#include "systemc.h"

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
        if (sc_is_running()) {
            wait(10, SC_NS);
        }
        #endif
        errorCode::fail(firstAssert, 1);
        endOfTestState::GetInstance().forceEndOfTest();
    }
    REAL_ASSERT; // Trigger to preserve callstack if RUNNING_IN_DEBUGGER, otherwise continue to sc_stop()
    wait(SC_ZERO_TIME);
    sc_stop();
    wait(SC_ZERO_TIME);
    sc_assert(false); // should not get here
}
