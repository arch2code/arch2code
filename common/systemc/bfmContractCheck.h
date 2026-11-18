#ifndef BFMCONTRACTCHECK_H
#define BFMCONTRACTCHECK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "logging.h"
#include "interfaceBase.h"
#include "q_assert.h"
#include <cstddef>
#include <format>
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

// Counts violations of the interface contract between a BFM and its HDL. The
// first is logged with its time and the total at end of simulation. A UVM run
// sets toUvm, which queues the first violation of every check not built
// warnOnly for the testbench module. It takes each with
// a2c_bfm_contract_break() and raises it as a UVM_ERROR, so a test can expect
// one with a report catcher. A violation the testbench never took fails the
// run at the end (failUntaken()). A check built failsRun fails the run at its
// first violation in every flow, UVM included, as one after which the model
// and the HDL disagree on a transfer.
struct bfmContractCheck {
    static inline bool toUvm = false;
    // A function-local static for the same clang 18.1.8 crash as hdlWokeMap().
    static std::vector<std::string> &uvmBreaks() {
        static std::vector<std::string> breaks;
        return breaks;
    }
    static inline std::size_t uvmTaken = 0;
    logBlock log_;
    const std::string what_;
    const std::string unit_;
    const bool warnOnly_;
    const bool failsRun_;
    uint64_t count_ = 0;
    bfmContractCheck(std::string name, std::string what, std::string unit, bool warnOnly = false, bool failsRun = false)
        : log_(name), what_(what), unit_(unit), warnOnly_(warnOnly), failsRun_(failsRun) {}
    void fail(const sc_time &edge, const std::string &detail = "") {
        if (count_++ == 0) {
            const std::string msg = std::format("{} at {}{}", what_, edge.to_string(), detail);
            log_.logPrint(msg, LOG_IMPORTANT);
            if (toUvm && !warnOnly_) {
                uvmBreaks().push_back(log_.getLogPrefix() + msg);
            }
            if (failsRun_) {
                errorCode::fail(log_.getLogPrefix() + msg);
            }
        }
    }
    void report(void) {
        if (count_ != 0) {
            log_.logPrint(std::format("{}, {} {} in total", what_, count_, unit_), LOG_IMPORTANT);
        }
    }
    static void failUntaken(void) {
        if (uvmTaken < uvmBreaks().size()) {
            errorCode::fail(std::format("{} BFM contract break(s) never reached UVM, the first: {}",
                                        uvmBreaks().size() - uvmTaken, uvmBreaks()[uvmTaken]));
        }
    }
};

struct bfmSameClockAnswer;

// The clock of each BFM, found through the channel its port binds. A model
// part that stands for RTL storage clocked like one of the model's ports
// takes that port's BFM clock from here; a channel with no BFM has none.
// A BFM registered with its bfmSameClockAnswer is also named by
// droveAt() when it drove a pin at a given time.
struct bfmClocks {
    struct entry {
        sc_port_base *port;
        const sc_in<bool> *clk;
        const bfmSameClockAnswer *answer;
    };
    // A function-local static for the same clang 18.1.8 crash as hdlWokeMap().
    static std::vector<entry> &all() {
        static std::vector<entry> entries;
        return entries;
    }
    static void add(sc_port_base &port, const sc_in<bool> &clk, const bfmSameClockAnswer *answer = nullptr) {
        all().push_back({&port, &clk, answer});
    }
    static const sc_in<bool> *of(sc_interface *chnl) {
        for (const entry &e : all()) {
            if (e.port->get_interface() == chnl) {
                return e.clk;
            }
        }
        return nullptr;
    }
    // The BFM and the channel its port binds, which carries the model port's name.
    static std::string describe(const entry &e) {
        const auto *chnl = dynamic_cast<const sc_object *>(e.port->get_interface());
        return std::format("{} on {}", e.port->get_parent_object()->name(), chnl != nullptr ? chnl->name() : "an unbound port");
    }
    static std::string portOf(const bfmSameClockAnswer *answer);
    static std::vector<std::string> droveAt(const sc_time &at, const bfmSameClockAnswer *except);
};

// The tail of a break of the sample-point precondition: the port, what was
// sampled when, and the BFM ports that drove a pin in that time step, the
// candidates for the combinational path.
inline std::string bfmPreconditionBreak(const bfmSameClockAnswer *self, const std::string &sampledWhat, const sc_time &sampled) {
    const std::vector<std::string> drove = bfmClocks::droveAt(sampled, self);
    std::string ports;
    for (const std::string &p : drove) {
        ports += (ports.empty() ? "" : ", ") + p;
    }
    return std::format(
        " ({}, {} at {}). The RTL breaks the precondition that on BFM ports an HDL ready, ack "
        "or read data does not depend combinationally on a pin another BFM drives; {}",
        bfmClocks::portOf(self), sampledWhat, sampled.to_string(),
        drove.empty() ? std::string("no other tracked BFM port drove a pin in the sample point's time step")
                      : "BFM ports that drove a pin in the sample point's time step: " + ports);
}

// A dst BFM completes the model's call at the sample point, when ready is
// high there, so the HDL must keep ready high to the next rising edge. A
// ready that falls in between leaves the model with a transfer the HDL never
// made, so it fails the run in every flow. BFM pins change up to and at the
// sample point, so RTL whose ready, ack or read data follows a pin another
// BFM drives combinationally can drop it after the BFM read it; the message
// names the BFM ports that drove a pin in that time step.
struct bfmReadyLowered : bfmContractCheck {
    bfmReadyLowered(std::string name)
        : bfmContractCheck(name, "HDL lowered ready after the sample point where the model's call completed", "clock edges",
                           false, true) {}
    void fail(const bfmSameClockAnswer *self, const sc_time &sampled) {
        bfmContractCheck::fail(sc_time_stamp(), bfmPreconditionBreak(self, "ready sampled high", sampled));
    }
};

// The read data a dst BFM hands the model at the sample point must still be
// on the pins at the next rising edge, where the HDL transfers it. Read data
// that changes in between gives the model a value the HDL never sent, so it
// fails the run in every flow, as bfmReadyLowered does.
template <typename PINS_T>
struct bfmReadDataChanged : bfmContractCheck {
    PINS_T sampled_{};
    sc_time sampledAt_;
    bfmReadDataChanged(std::string name)
        : bfmContractCheck(name, "HDL changed read data after the sample point where the model received it", "clock edges",
                           false, true) {}
    void sample(const PINS_T &pins) {
        sampled_ = pins;
        sampledAt_ = sc_time_stamp();
    }
    // At the rising edge after sample(), outside reset.
    void check(const bfmSameClockAnswer *self, const PINS_T &pins) {
        if (!(pins == sampled_)) {
            fail(sc_time_stamp(), bfmPreconditionBreak(self, "read data sampled", sampledAt_));
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
    // A function-local static: an inline data member with a dynamic initializer in this header
    // crashes clang 18.1.8 when it compiles a generated Base module's PCM to an object.
    static std::unordered_map<const sc_object *, wake> &hdlWokeMap() {
        static std::unordered_map<const sc_object *, wake> woke;
        return woke;
    }
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
        hdlWokeMap()[sc_get_current_process_handle().get_process_object()] = {sc_time_stamp(), sc_delta_count()};
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
        const auto woke = hdlWokeMap().find(caller);
        const bool hdlWoke = woke != hdlWokeMap().end() && woke->second.time == callTime && callDelta >= woke->second.delta;
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
// The same sample point serves a dst BFM, which completes a send there (see
// waitTaken()). The high phase is measured at every falling edge, so the BFM
// follows the clock it is given. rose() may be called by both a rising-edge
// method and a thread woken by that edge, in either order.
struct bfmSameClockAnswer {
    sc_time rise_;
    sc_time high_;
    sc_time drove_;
    sc_time droveBefore_;
    bool hasDriven_ = false;
    bool hasDrivenBefore_ = false;
    sc_time sampled_;
    void rose() { rise_ = sc_time_stamp(); }
    void fell() { high_ = sc_time_stamp() - rise_; }
    bool drove(const sc_time &at) const { return (hasDriven_ && drove_ == at) || (hasDrivenBefore_ && droveBefore_ == at); }
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
        driving();
    }
    // Called at any point in a clock. False when the clock is low or this
    // clock's sample point has passed.
    bool waitSamplePointInClock(const sc_in<bool> &clk) {
        const sc_time step = sc_get_time_resolution();
        if (!clk.read() || high_ <= step) {
            return false;
        }
        const sc_time at = rise_ + high_ - step;
        const sc_time now = sc_time_stamp();
        if (now > at) {
            return false;
        }
        if (now < at) {
            wait(at - now);
        }
        return clk.read();
    }
    // Lets a dst BFM complete the model's send when the HDL's transfer of the
    // beat on its pins becomes certain: ready is high at the sample point,
    // and no pin changes before the next rising edge. The model's next call
    // then reaches its port before that edge, so a model that sends and then
    // receives moves a beat per clock, as RTL whose ready follows its
    // output's ready does. True at that sample point. False at a rising edge
    // that took the beat with no such sample point, where the send completes
    // instead. edge() runs at each rising edge waited on.
    template <typename READY, typename EDGE>
    bool waitTaken(const sc_in<bool> &clk, READY ready, EDGE edge) {
        while (true) {
            if (waitSamplePointInClock(clk) && ready()) {
                sampled_ = sc_time_stamp();
                return true;
            }
            wait(clk.posedge_event());
            rose();
            edge();
            if (ready()) {
                return false;
            }
        }
    }
    // Called by a src BFM that has driven ready low after a rising edge. A
    // model receive that starts by this clock's sample point, such as one
    // that follows a send a dst BFM completed there, goes on the pins at
    // once. True once ready() holds by the sample point, false after it.
    // entered fires as a receive starts.
    template <typename READY>
    bool waitReadyInClock(const sc_in<bool> &clk, const sc_event &entered, READY ready) {
        const sc_time step = sc_get_time_resolution();
        if (high_ <= step) {
            return false;
        }
        const sc_time last = rise_ + high_ - step;
        while (clk.read() && sc_time_stamp() <= last) {
            if (ready()) {
                driving();
                return true;
            }
            wait(last + step - sc_time_stamp(), entered);
        }
        return false;
    }
    // The rising edge after waitTaken() returned true. False when ready fell
    // before it, so the HDL did not take the beat; outside reset lowered
    // fails the run.
    template <typename READY>
    bool waitTakenEdge(const sc_in<bool> &clk, const sc_in<bool> &rst_n, READY ready, bfmReadyLowered &lowered) {
        wait(clk.posedge_event());
        rose();
        if (ready()) {
            return true;
        }
        if (rst_n.read()) {
            lowered.fail(this, sampled_);
        }
        return false;
    }
    // Called as the BFM changes its pins, for bfmReadyLowered. The time
    // before the latest is kept too: a BFM whose transfer was certain at the
    // sample point drives its next beat at the rising edge, in the delta
    // where waitTakenEdge() asks who drove at the sample point.
    void driving() {
        const sc_time now = sc_time_stamp();
        if (hasDriven_ && drove_ == now) {
            return;
        }
        droveBefore_ = drove_;
        hasDrivenBefore_ = hasDriven_;
        drove_ = now;
        hasDriven_ = true;
    }
};

// Lets an ack-style, APB or LMMI dst BFM complete the model's call at the
// sample point while its own thread keeps the request pins up to the edge
// that takes them. The completion can wait out the channel's timed delay
// past that edge, so it runs in a thread of its own.
struct bfmCompleter {
    std::function<void()> complete_;
    sc_event start_;
    sc_event done_;
    bool busy_ = false;
    bfmCompleter(std::function<void()> complete) : complete_(std::move(complete)) {
        sc_core::sc_spawn([this]() { this->thread(); });
    }
    void start() {
        busy_ = true;
        start_.notify();
    }
    void waitDone() {
        while (busy_) {
            wait(done_);
        }
    }
private:
    void thread() {
        while (true) {
            wait(start_);
            complete_();
            busy_ = false;
            done_.notify();
        }
    }
};

inline std::string bfmClocks::portOf(const bfmSameClockAnswer *answer) {
    for (const entry &e : all()) {
        if (e.answer == answer) {
            return describe(e);
        }
    }
    return "unregistered";
}

inline std::vector<std::string> bfmClocks::droveAt(const sc_time &at, const bfmSameClockAnswer *except) {
    std::vector<std::string> ports;
    for (const entry &e : all()) {
        if (e.answer != nullptr && e.answer != except && e.answer->drove(at)) {
            ports.push_back(describe(e));
        }
    }
    return ports;
}

// Only a channel built with BACKPRESSURE_NONE promises that the consumer never
// lowers rdy.
inline bool bfmNoBackpressure(sc_interface *intf, const std::string &bfm) {
    auto *chnl = dynamic_cast<interfaceBase *>(intf);
    Q_ASSERT_CTX(chnl != nullptr, bfm, "BFM is bound to an interface that is not an interfaceBase channel");
    return chnl->getTimedDelayRule() == TIMED_DELAY_NO_BACKPRESSURE;
}

#endif /* BFMCONTRACTCHECK_H */
