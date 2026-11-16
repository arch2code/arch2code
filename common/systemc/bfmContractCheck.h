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
#include <unordered_map>
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

// Reports a port whose model waits on the clock between port calls, which a
// transactional model must not do. Such a model comes back to the port on the
// first edge after each transfer, too late to transfer on it, so the port
// moves one beat per two clocks. A return counts only if the model called the
// port in that edge's own delta or earlier, which is what a model waiting on
// the clock does. A model woken by another channel's delta notification runs
// later and is not counted. Nor is a call from a model thread that a memory
// BFM woke in that delta, whose channel notifies immediately: the HDL paces
// that model, not a wait of its own. The report is logged once per port and
// never fails a run, UVM included: the model still runs, at the rate its own
// waits allow.
struct bfmClockPaced {
    static constexpr int threshold = 32;
    struct wake {
        sc_time time;
        sc_dt::uint64 delta;
    };
    static inline std::unordered_map<const sc_object *, wake> hdlWoke_;
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
    // Called in a model thread that a channel call from a BFM has just woken
    // with an immediate notification.
    static void hdlWokeModel(void) {
        hdlWoke_[sc_get_current_process_handle().get_process_object()] = {sc_time_stamp(), sc_delta_count()};
    }
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
    void transfer(const sc_time &now, const sc_time &callTime, sc_dt::uint64 callDelta, const sc_object *caller) {
        if (told_) {
            return;
        }
        const auto woke = hdlWoke_.find(caller);
        const bool hdlWoke = woke != hdlWoke_.end() && woke->second.time == callTime && callDelta >= woke->second.delta;
        const bool paced = edgeAfterKnown_ && callTime == edgeAfter_ && callDelta <= edgeAfterDelta_ && !hdlWoke;
        run_ = paced ? run_ + 1 : 0;
        if (run_ == threshold) {
            told_ = true;
            const std::string msg = std::format("port {}: the model came back exactly one clock after each of {} "
                                                "transfers in a row, so it waits on the clock between port calls and "
                                                "the port moves one beat per two clocks. A transactional model must "
                                                "not wait on clock edges: remove the wait from the model", port_, threshold);
            log_.logPrint(msg, LOG_IMPORTANT);
        }
        transfer_ = now;
        started_ = true;
        edgeAfterKnown_ = false;
    }
};

// An HDL requester on a handshake where the BFM answers holds its request and
// its data from the edge the BFM takes them to the edge the BFM completes the
// transfer. The model has the transfer from the take on, so a request the HDL
// drops or changes in between is one the model took and the HDL did not
// complete. The driver checks each edge it waits on itself; the monitor checks
// the edges that pass while the driver is blocked in the model's call.
template <typename PINS_T>
struct bfmHeldRequest {
    bfmContractCheck check_;
    PINS_T taken_{};
    sc_time takeTime_;
    bool inCall_ = false;
    bfmHeldRequest(std::string name)
        : check_(name, "HDL dropped or changed a request between the edge the BFM took it and the edge it completed",
                 "clock edges") {}
    void take(const PINS_T &pins) {
        taken_ = pins;
        takeTime_ = sc_time_stamp();
    }
    void check(bool held, const PINS_T &pins) {
        if (!held || !(pins == taken_)) {
            check_.fail(sc_time_stamp());
        }
    }
    void monitor(bool held, const PINS_T &pins) {
        if (inCall_ && sc_time_stamp() > takeTime_) {
            check(held, pins);
        }
    }
};

// Lets an ack-style src BFM answer a request in the clock the HDL raised it,
// as a destination whose ack follows the request combinationally does. Every
// source changes its pins between a rising edge and the next falling edge, so
// the BFM takes the request one time-resolution step before the falling edge.
// A model that answers in zero time then has ack on the pins at the falling
// edge, where a UVM monitor samples, and the next rising edge transfers it.
// The high phase is measured at every falling edge, so the BFM follows the
// clock it is given.
struct bfmSameClockAnswer {
    sc_time rise_;
    sc_time high_;
    void rose() { rise_ = sc_time_stamp(); }
    void fell() { high_ = sc_time_stamp() - rise_; }
    // Called at a rising edge. False, with the request not to be taken in
    // this clock, until a high phase has been measured, or when the clock
    // fell earlier than the last one did.
    bool waitSamplePoint(const sc_in<bool> &clk) {
        const sc_time step = sc_get_time_resolution();
        if (high_ <= step) {
            return false;
        }
        wait(high_ - step);
        return clk.read();
    }
    // An answer the model gives while the clock is high goes on the pins at
    // once, before the falling edge. A later one goes on them one step after
    // the next rising edge, so the pins never change between a falling edge
    // and the rising edge after it.
    void waitDrivePoint(const sc_in<bool> &clk) {
        if (!clk.read()) {
            wait(clk.posedge_event());
            wait(sc_get_time_resolution());
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
