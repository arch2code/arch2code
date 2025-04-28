#ifndef TIMEDDELAY_H
#define TIMEDDELAY_H

#include "randFactory.h"
#include "q_assert.h"

enum timedDelayMode {
    TIMED_DELAY_FIXED_INIT, TIMED_DELAY_RAND_INIT, TIMED_DELAY_RAND_FULL
};

class timedDelayBase {
public:
    virtual void setTimed(int nsec, timedDelayMode mode) = 0;
    virtual void delay(bool waitOnZero=false) = 0;
    virtual sc_time getNextDelay(void) = 0;
    virtual ~timedDelayBase() {}
};


class timedDelay : public timedDelayBase {
public:

    timedDelay(std::string s) {
        m_hash = randFactory::str2hash(s);
    }

    void setTimed(int nsec, timedDelayMode mode) override {
        m_delayMode = mode;
        if (m_delayMode == TIMED_DELAY_FIXED_INIT) {
            m_delayTime = sc_time(nsec, SC_NS);
        } else {
            m_delayRNG = randFactory::createUniformRandDistrObj(m_hash, 0, nsec);
            m_delayTime = sc_time(m_delayRNG->generate(), SC_NS);
        }
    }

    void delay(bool waitOnZero=false) override {
        if ((m_delayTime > SC_ZERO_TIME) || waitOnZero) {
            wait(m_delayTime);
        }
        m_delayTime = getNextDelay();
    }

    sc_time getNextDelay(void) override {
        if (m_delayMode == TIMED_DELAY_RAND_FULL) {
            return sc_time(m_delayRNG->generate(), SC_NS);
        } else {
            return m_delayTime;
        }
    }

private:

    std::size_t m_hash;
    sc_time m_delayTime = SC_ZERO_TIME;
    timedDelayMode m_delayMode = TIMED_DELAY_FIXED_INIT;
    std::unique_ptr<randObject> m_delayRNG;

};

class timedDelayShared : public timedDelayBase {
public:
    // constructor for primary object - note primary interface is the master
    timedDelayShared(std::string s) {
        m_delay = std::make_unique<timedDelay>(s);
    }
    // constructor for secondary object - secondary interface must come after the primary - ie dependent interface
    timedDelayShared(std::shared_ptr<timedDelayShared> shared) {
        Q_ASSERT_CTX_NODUMP(shared != nullptr, "", "secondary must be called with a valid object");
        m_delayShared = shared;
    }
    void setTimed(int nsec, timedDelayMode mode) override {
        if (m_delay) {
            m_delay->setTimed(nsec, mode);
        }
    }
    void delay(bool waitOnZero=false) override {
        if (m_delay) {
            m_delayTime = m_delay->getNextDelay();
        } else {
            m_delayTime = m_delayShared->getLastDelay();
        }
        if ((m_delayTime > SC_ZERO_TIME) || waitOnZero) {
            wait(m_delayTime);
        }

    }
    sc_time getNextDelay(void) override {
        if (m_delay) {
            m_delayTime = m_delay->getNextDelay();
        } else {
            m_delayTime = m_delayShared->getLastDelay();
        }
        return m_delayTime;
    }
    sc_time getLastDelay(void) {
        return m_delayTime;
    }


private:
    std::unique_ptr<timedDelay> m_delay;
    std::shared_ptr<timedDelayShared> m_delayShared;
    sc_time m_delayTime = SC_ZERO_TIME;
};

#endif // TIMEDDELAY_H
