#ifndef MODELCOMM_H
#define MODELCOMM_H

#include <boost/lockfree/spsc_queue.hpp>
#include "bitTwiddling.h"
#include <algorithm>

struct regAccessSt
{
    regAccessSt(uint32_t _address, uint32_t _value, bool _isWrite) :
        address(_address),
        value(_value),
        isWrite(_isWrite) {};
    regAccessSt() {};
    uint32_t address;
    uint32_t value;
    bool isWrite;
};
struct regReadResponseSt
{
    regReadResponseSt(uint32_t _value) :
        value(_value) {};
    regReadResponseSt() {};
    uint32_t value;
};

struct boostQueueInterruptSt
{
    boostQueueInterruptSt() {};
};
#define BOOST_MESSAGES_MAX 32
extern boost::lockfree::spsc_queue<regAccessSt, boost::lockfree::capacity<BOOST_MESSAGES_MAX> > regAccessQueue;
extern boost::lockfree::spsc_queue<regReadResponseSt, boost::lockfree::capacity<BOOST_MESSAGES_MAX> > regReadResponseQueue;
extern boost::lockfree::spsc_queue<boostQueueInterruptSt, boost::lockfree::capacity<BOOST_MESSAGES_MAX> > fwInterruptQueue;


// in a pop, we are reading from currentHead and incrementing it and updating the hw
// add temporary check for hw tail to ensure we don't read and empty queue


#endif //MODELCOMM_H
