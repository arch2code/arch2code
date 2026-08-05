#include "fwlog.h"
#include "asyncEvent.h"
#include "regRdWr.h"
#include "modelComm.h"
#include "workerThread.h"
#include <thread>

// instantiate the register queues
boost::lockfree::spsc_queue<regAccessSt, boost::lockfree::capacity<BOOST_MESSAGES_MAX> > regAccessQueue;
boost::lockfree::spsc_queue<regReadResponseSt, boost::lockfree::capacity<BOOST_MESSAGES_MAX> > regReadResponseQueue;
boost::lockfree::spsc_queue<boostQueueInterruptSt, boost::lockfree::capacity<BOOST_MESSAGES_MAX> > fwInterruptQueue;

void regWrite32(uint64_t address, uint32_t value)
{
    static std::shared_ptr<ThreadSafeEvent> regWriteEvent = ThreadSafeEventFactory::newEvent("regWriteEvent");
    static std::shared_ptr<workerEvent> fwEvent(workerFactory::getWorkerEvent("fw"));
    regAccessSt regAccess(address, value, true);
    regAccess.isWrite = true;
    while (!regAccessQueue.push(regAccess)) {
        fwEvent->wait("regWrite32");
    }
    regWriteEvent->notify();
}

void regWrite64(uint64_t address, uint64_t value)
{
    uint32_t* uint32Ptr1 = reinterpret_cast<uint32_t*>(&value);
    uint32_t* uint32Ptr2 = uint32Ptr1 + 1;
    regWrite32(address, *uint32Ptr1);
    regWrite32(address + sizeof(uint32_t), *uint32Ptr2);
}

uint32_t regRead32(uint64_t address)
{
    static std::shared_ptr<ThreadSafeEvent> regWriteEvent = ThreadSafeEventFactory::newEvent("regWriteEvent");
    static std::shared_ptr<workerEvent> fwEvent(workerFactory::getWorkerEvent("fw"));
    regAccessSt regAccess(address, 0, false);
    while (!regAccessQueue.push(regAccess)) {
        fwEvent->wait("regRead32QueueFull");
    }
    regWriteEvent->notify();
    int timeout = 100000;
    while (regReadResponseQueue.empty()) {
        fwEvent->wait("regRead32");
        timeout--;
        Q_ASSERT_CTX(timeout > 0, "", "Timeout waiting for reg read response");
    }
    regReadResponseSt response;
    regReadResponseQueue.pop(response);
    return response.value;
}

uint64_t regRead64(uint64_t address)
{
    static std::shared_ptr<ThreadSafeEvent> regWriteEvent = ThreadSafeEventFactory::newEvent("regWriteEvent");
    static std::shared_ptr<workerEvent> fwEvent(workerFactory::getWorkerEvent("fw"));
    regAccessSt regAccess(address, 0, false);
    while (!regAccessQueue.push(regAccess)) {
        fwEvent->wait("regRead64QueueFull1");
    }
    regAccess.address += sizeof(uint32_t);
    while (!regAccessQueue.push(regAccess)) {
        fwEvent->wait("regRead64QueueFull2");
    }
    regWriteEvent->notify();
    int timeout = 100000;
    int responses = 0;
    uint64_t value = 0;
    uint32_t* uint32Ptr = reinterpret_cast<uint32_t*>(&value);
    while (responses < 2) {
        while (regReadResponseQueue.empty()) {
            fwEvent->wait("regRead64");
            timeout--;
            Q_ASSERT_CTX(timeout > 0, "", "Timeout waiting for reg read response");
        }
        regReadResponseSt response;
        regReadResponseQueue.pop(response);
        responses++;
        *uint32Ptr = response.value;
        uint32Ptr++;
    }
    return value;
}