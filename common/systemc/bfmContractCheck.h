#ifndef BFMCONTRACTCHECK_H
#define BFMCONTRACTCHECK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "logging.h"
#include "interfaceBase.h"
#include "q_assert.h"
#include <cstddef>
#include <format>
#include <string>
#include <vector>

// Counts violations of the interface contract between a BFM and its HDL. The
// first is logged with its time and the total at end of simulation. A UVM run
// sets toUvm, which queues the first violation of every check not built
// warnOnly for the testbench module. It takes each with
// a2c_bfm_contract_break() and raises it as a UVM_ERROR, so a test can expect
// one with a report catcher. A violation the testbench never took fails the
// run at the end (failUntaken()).
struct bfmContractCheck {
    static inline bool toUvm = false;
    static inline std::vector<std::string> uvmBreaks;
    static inline std::size_t uvmTaken = 0;
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
            if (toUvm && !warnOnly_) {
                uvmBreaks.push_back(log_.getLogPrefix() + msg);
            }
        }
    }
    void report(void) {
        if (count_ != 0) {
            log_.logPrint(std::format("{}, {} {} in total", what_, count_, unit_), LOG_IMPORTANT);
        }
    }
    static void failUntaken(void) {
        if (uvmTaken < uvmBreaks.size()) {
            errorCode::fail(std::format("{} BFM contract break(s) never reached UVM, the first: {}",
                                        uvmBreaks.size() - uvmTaken, uvmBreaks[uvmTaken]));
        }
    }
};

// Logs one notice per port when the model behind a BFM comes back to the port
// on the first edge after each transfer, too late to transfer on it, so the
// port moves one beat per two clocks. A return counts only if the model called
// the port in that edge's own delta or earlier, which is what a model waiting
// on the clock does. A model woken by another channel's delta notification
// runs later and is not counted. One woken by an immediate notification from a
// process at the edge, such as a memory BFM's request(), is counted, so the
// notice reports the pacing and does not claim a wait. It never fails the run
// and never reaches UVM.
struct bfmClockPaced {
    static constexpr int threshold = 32;
    logBlock log_;
    std::string port_;
    sc_time transfer_;
    sc_time prevEdge_;
    sc_time edgeAfter_;
    sc_dt::uint64 edgeAfterDelta_ = 0;
    bool started_ = false;
    bool edgeAfterKnown_ = false;
    int run_ = 0;
    bool told_ = false;
    bfmClockPaced(std::string name) : log_(name) {}
    // The method and the driver wake on the same edge in either order. The
    // driver records a transfer at its own edge, so the method's previous edge
    // equals it only on the first edge after the transfer.
    void edge(const sc_time &now) {
        if (started_ && prevEdge_ == transfer_) {
            edgeAfter_ = now;
            edgeAfterDelta_ = sc_delta_count();
            edgeAfterKnown_ = true;
        }
        prevEdge_ = now;
    }
    void transfer(const sc_time &now, const sc_time &callTime, sc_dt::uint64 callDelta) {
        if (told_) {
            return;
        }
        const bool paced = edgeAfterKnown_ && callTime == edgeAfter_ && callDelta <= edgeAfterDelta_;
        run_ = paced ? run_ + 1 : 0;
        if (run_ == threshold) {
            told_ = true;
            log_.logPrint(std::format("port {}: the port moves one beat per two clocks, because the model came "
                                      "back exactly one clock after each of {} transfers in a row. If the model "
                                      "waits on the clock between port calls, removing that wait restores one "
                                      "beat per clock. A model woken by another port that the HDL paces, such as "
                                      "a memory port, can show the same pattern and needs no change", port_, threshold), LOG_IMPORTANT);
        }
        transfer_ = now;
        started_ = true;
        edgeAfterKnown_ = false;
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
