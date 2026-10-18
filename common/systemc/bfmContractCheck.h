#ifndef BFMCONTRACTCHECK_H
#define BFMCONTRACTCHECK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "logging.h"
#include "interfaceBase.h"
#include "q_assert.h"
#include <format>
#include <string>

// Counts violations of the interface contract between a BFM and its HDL. The
// first is logged with its time and the total at end of simulation. A flow
// that sets failOnBreak also fails the run at the first violation of every
// check not built warnOnly.
struct bfmContractCheck {
    static inline bool failOnBreak = false;
    logBlock log_;
    const std::string what_;
    const std::string unit_;
    const bool warnOnly_;
    uint64_t count_ = 0;
    bfmContractCheck(std::string name, std::string what, std::string unit, bool warnOnly = false)
        : log_(name), what_(what), unit_(unit), warnOnly_(warnOnly) {}
    void fail(const sc_time &edge) {
        if (count_++ == 0) {
            const std::string msg = std::format("{} at {}", what_, edge.to_string());
            log_.logPrint(msg, LOG_IMPORTANT);
            if (failOnBreak && !warnOnly_) {
                errorCode::fail(log_.getLogPrefix() + msg);
            }
        }
    }
    void report(void) {
        if (count_ != 0) {
            log_.logPrint(std::format("{}, {} {} in total", what_, count_, unit_), LOG_IMPORTANT);
        }
    }
};

// Only a channel built with BACKPRESSURE_NONE promises that the consumer never
// lowers rdy.
inline bool bfmNoBackpressure(sc_interface *intf, const std::string &bfm) {
    auto *chnl = dynamic_cast<interfaceBase *>(intf);
    Q_ASSERT_CTX(chnl != nullptr, bfm, "BFM is bound to an interface that is not an interfaceBase channel");
    return chnl->getTimedDelayRule() == TIMED_DELAY_NO_BACKPRESSURE;
}

#endif /* BFMCONTRACTCHECK_H */
