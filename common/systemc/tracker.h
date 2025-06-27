#ifndef TRACKER_H
#define TRACKER_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <vector>
#include <string>
#include <type_traits>
#include <fmt/format.h>
#include "logging.h"
#include "trackerBase.h"
#include <map>
#include "multiCycleBase.h"
#include <cstring>
#include <mutex>
#include "instanceFactory.h"
#include <sstream>
#include <iomanip>  // For std::hex

// SFINAE helper to check if T has std::string prt(void) method
template<typename T, typename = void>
struct has_prt_method : std::false_type {};

template<typename T>
struct has_prt_method<T, std::void_t<
    decltype(std::declval<T>().prt())
>> : std::is_same<std::string, decltype(std::declval<T>().prt())> {};

// tracker can use a shared counter to allow multiple trackers to avoid the same sequence number, or use there own counter
template <class T>
class tracker : public trackerBase
{
    static_assert(has_prt_method<T>::value, 
        "Type T must have a 'std::string prt(void)' method");
public:
    // private counter use case
    // size : number of tags
    // name : tracker name used for logging
    // prefix : prefix for the tag string, used to distinguish between different trackers typically this wants to be uniquely searchable eg 'C#'
    // prtTag : function to print the tag, typically this is a lambda provides any useful formatting
    // internalBufferSize : size of the internal buffer for the backdoor pointer, if 0 then no internal buffer is allocated
    tracker(const int size, const std::string &name, const std::string &prefix, std::function<std::string(const int tag)> prtTag, int internalBufferSize = 0) :
        prefix_(prefix),
        pSequenceCounter_(std::make_shared<uint64_t>(0)),
        size_(size),
        tags_(size, nullptr),
        valid_(size, false),
        allocCount_(size, 0),
        sequenceNo_(size, 0),
        dataBackdoor_(size, nullptr),
        lenBackdoor_(size, 0),
        name_(name),
        lastString_(size),
        prtTag_(prtTag),
        log_(name)
        {
            initInternalBuffers(internalBufferSize);
        }
    // shared counter use case
    // as above but with a shared pointer to a counter
    // counter : shared pointer to a counter that will be used to generate unique sequence numbers for the tags
    tracker(const int size, std::shared_ptr<uint64_t> counter, const std::string name, const std::string &prefix, std::function<std::string(const int tag)> prtTag, int internalBufferSize = 0) :
        prefix_(prefix),
        pSequenceCounter_(counter),
        size_(size),
        tags_(size, nullptr),
        valid_(size, false),
        allocCount_(size, 0),
        sequenceNo_(size, 0),
        dataBackdoor_(size, nullptr),
        lenBackdoor_(size, 0),
        name_(name),
        lastString_(size),
        prtTag_(prtTag),
        log_(name)
        {
            initInternalBuffers(internalBufferSize);
        }
    // for debug use cases set noassert to true to avoid asserts
    std::string prt(const int tag, bool noAssert=false) override
    {
        if (noAssert && !valid_[tag]) {
            return "{Invalid Tag}";
        }
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        uint64_t seq = sequenceNo_[tag];
        std::stringstream ss;
        if (tags_[tag] != nullptr) {
            ss << prefix_ << std::hex << seq << "{" << tags_[tag]->prt() << "}";
        } else {
            ss << prefix_ << std::hex << seq << (valid_[tag]==true ? "valid tag" : "invalid tag" ) << "{nullptr}";
        }
        return ss.str();
    }
    std::string prt(const int tag, const std::string &s) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x} [{}]", tag, s ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x} [{}]", tag, s ));
        uint64_t seq = sequenceNo_[tag];
        std::stringstream ss;
        if (tags_[tag] != nullptr) {
            ss << s << " " << prefix_ << std::hex << seq << "{" << tags_[tag]->prt() << "}";
        } else {
            ss << s << " "  << prefix_ << std::hex << seq << (valid_[tag]==true ? "valid tag" : "invalid tag" ) << "{nullptr}";
        }
        if (saveLastString_) {
            lastString_[tag] = ss.str();
        }
        return ss.str();
    }
    std::string prt(const int tag, const std::string &s, const std::string &lastPrefix) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x} [{}]", tag, s ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x} [{}]", tag, s ));
        uint64_t seq = sequenceNo_[tag];
        std::stringstream ss;
        if (tags_[tag] != nullptr) {
            ss << prefix_ << std::hex << seq << "{" << tags_[tag]->prt() << "}" << s;
        } else {
            ss << prefix_ << std::hex << seq << (valid_[tag]==true ? "valid tag" : "invalid tag" ) << "{nullptr}" << s;
        }
        if (saveLastString_) {
            lastString_[tag] = lastPrefix + ss.str();
        }
        return ss.str();
    }
    // version of prt that uses [] instead of {} to simplify parsing output
    std::string getString(const int tag) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        uint64_t seq = sequenceNo_[tag];
        std::stringstream ss;
        if (tags_[tag] != nullptr) {
            ss << prefix_ << std::hex << seq << "[" << tags_[tag]->prt() << "]";
        } else {
            ss << prefix_ << std::hex << seq << (valid_[tag]==true ? "valid tag" : "invalid tag" ) << "[nullptr]";
        }
        return ss.str();
    }
    std::string getString(const int tag, const std::string &s) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x} [{}]", tag, s));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x} [{}]", tag, s));
        uint64_t seq = sequenceNo_[tag];
        std::stringstream ss;
        if (tags_[tag] != nullptr) {
            ss << prefix_ << std::hex << seq << "[" << tags_[tag]->prt() << "]" << s;
        } else {
            ss << prefix_ << std::hex << seq << (valid_[tag]==true ? "valid tag" : "invalid tag" ) << "[nullptr]" << s;
        }
        return ss.str();
    }
    void saveLastString(bool val) override
    {
        saveLastString_ = val;
    }
    std::string getLastString(const int tag) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        return lastString_[tag];
    }
    void alloc(const int tag, std::shared_ptr<T> element, const int useCount=2)
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        allocCount_[tag] += useCount;
        Q_ASSERT_NODUMP(allocCount_[tag] <= 3, fmt::format("Too many allocs tag 0x{:x}", tag ));
        // override the existing tracker info with the programatic one
        if (element != nullptr) {
            tags_[tag] = element;
        }
        if (!valid_[tag])
        {
            valid_[tag] = true;
            sequenceNo_[tag] = (*pSequenceCounter_)++;
            count_++;
            std::stringstream ss;
            ss << "tagAlloc:" << prefix_ << std::hex << sequenceNo_[tag] << "{" << tags_[tag]->prt() << "}" << prtTag_(tag);
            log_.logPrint(ss.str(), LOG_IMPORTANT);
        }
    }
    void autoAlloc(const int tag, const std::string &trackerString, const int useCount) override
    {
        if (!valid_[tag])
        {
            alloc(tag, std::make_shared<T>(trackerString), useCount);
        } else {
            alloc(tag, nullptr, useCount);
        }
    }
    void dealloc(const int tag, const int useCount=2)
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP((allocCount_[tag]-useCount) >= 0, fmt::format("Too many deallocs tag 0x{:x}", tag ));
        // in case interface already deallocated the tag
        allocCount_[tag] -= useCount;
        if (allocCount_[tag] == 0)
        {
            std::stringstream ss;
            ss << "tagDealloc:" << prefix_ << std::hex << sequenceNo_[tag] << "{" << tags_[tag]->prt() << "}" << prtTag_(tag) ;
            log_.logPrint(ss.str(), LOG_IMPORTANT);
            tags_[tag].reset();
            valid_[tag] = false;
            count_--;
        }
    }
    void autoDealloc(const int tag, const int useCount) override
    {
        dealloc(tag, useCount);
    }
    inline std::shared_ptr<T> info(const int tag)
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        return(tags_[tag]);
    }
    uint64_t getLen(const int tag) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        return (lenBackdoor_[tag]);
    }
    void setLen(const int tag, const uint64_t len) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        lenBackdoor_[tag] = len;
    }
    uint8_t * getBackdoorPtr(const int tag) override
    {
        BOOST_ASSERT(valid_[tag] );
        return (dataBackdoor_[tag]);
    }
    // same as getBackdoorPtr but without valid check for t0 initialization use cases
    uint8_t * initGetBackdoorPtr(const int tag) override
    {
        return (dataBackdoor_[tag]);
    }
    void setBackdoorPtr(const int tag, uint8_t * ptr) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        dataBackdoor_[tag] = ptr;
    }
    // same as setBackdoorPtr but without valid check for t0 initialization use cases
    void initBackdoorPtr(const int tag, uint8_t * ptr) override
    {
        dataBackdoor_[tag] = ptr;
    }
    // api to allow configuring the backdoor buffer size different for different tags
    void initBackdoorBuffer(const int tag, uint32_t size) override
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        internalBuffers[tag] = std::make_unique<std::vector<uint8_t>>(size, 0);
        dataBackdoor_[tag] = internalBuffers[tag]->data();
        lenBackdoor_[tag] = size;
    }
    int getSequenceNo(const int tag)
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        return(sequenceNo_[tag]);
    }
    void dump(void) override
    {
        logDirect(fmt::format("Tracker: {} has {} tags allocated", name_, count_), LOG_IMPORTANT);
        if (!saveLastString_) {
            for (int i=0; i<size_; i++)
            {
                if (valid_[i])
                {
                    logDirect(fmt::format("{} dump:0x{:x} {}", name_, i, prt(i)), LOG_IMPORTANT);
                }
            }
        } else {
            for (int i=0; i<size_; i++)
            {
                if (valid_[i])
                {
                    logDirect(fmt::format("{} dump:0x{:x} {}", name_, i, lastString_[i]), LOG_IMPORTANT);
                }
            }
        }
    }
    int get_tracker_size(void) const override
    {
        return size_;
    }
    bool is_valid(const int tag) const override
    {
        return valid_[tag];
    }
    std::shared_ptr<T> getTagRef(const int tag)
    {
        Q_ASSERT_NODUMP(tag < size_, fmt::format("Attempted to use out of range tag 0x{:x}", tag ));
        Q_ASSERT_NODUMP(valid_[tag], fmt::format("Attempted to use unallocated tag 0x{:x}", tag ));
        return tags_[tag];
    }

private:
    // for use cases where the buffer size is common for all tags
    void initInternalBuffers(int internalBufferSize)
    {
        internalBuffers.resize(size_);
        if (internalBufferSize == 0)
        {
            return;
        }
        for (int i = 0; i < size_; i++)
        {
            internalBuffers[i] = std::make_unique<std::vector<uint8_t>>(internalBufferSize);
            dataBackdoor_[i] = internalBuffers[i]->data();
        }
    }
    std::string name() { return name_; }
    const std::string prefix_;
    std::shared_ptr<uint64_t> pSequenceCounter_;
    const int size_; // number of tags, and size of all the vectors
    std::vector<std::shared_ptr<T>> tags_;
    std::vector<bool> valid_;
    std::vector<int> allocCount_;
    std::vector<uint64_t> sequenceNo_;
    std::vector<uint8_t *> dataBackdoor_;
    std::vector<uint64_t> lenBackdoor_;
    std::string name_;
    std::vector<std::string> lastString_;
    std::vector< std::unique_ptr< std::vector< uint8_t > > > internalBuffers;
    int count_ = 0;
    std::function<std::string(const int tag)> prtTag_;
    logBlock log_;
    bool saveLastString_=false;
};

class trackerCollection {
public:
    // singleton pattern
    static trackerCollection &GetInstance() {
        static std::mutex m_mutex;
        std::lock_guard<std::mutex> lock(m_mutex);
        static trackerCollection instance;
        return instance;
    }
    void addTracker(const char* name_, std::shared_ptr<trackerBase> tracker)
    {
        std::string name(name_);
        auto result = trackers.insert(std::pair<std::string, std::shared_ptr<trackerBase>>(name, tracker));
        if (result.second == false)
        {
            Q_ASSERT_CTX(false, name, "Tracker already exists")
        }
    }
    std::shared_ptr<trackerBase> getTracker(const char* name_, bool noAssert=false)
    {

        if (name_[0] == '\0') {
            // Empty string
            return nullptr;
        }

        std::string name(name_);
        // check the string begins with "tracker:" and take the rest of the string as the tracker name
        if (name.find("tracker:") == 0)
        {
            name = name.substr(8);
        } else {
            // if we get here then its either the programatic use of the name, or its the special length case from getValueType() function
            if (name == "length")
            {
                return nullptr;
            }
        }

        auto it = trackers.find(name);
        if (it == trackers.end())
        {
            Q_ASSERT_CTX(noAssert, name, "Tracker not found")
            return nullptr;
        }
        return(it->second);
    }
    void dump(void)
    {
        for (auto it = trackers.begin(); it != trackers.end(); ++it)
        {
            it->second->dump();
        }
    }
    void alloc(const char* name, int tag, const char* thread_string)
    {
        std::string name_(name);
        auto it = trackers.find(name_);
        if (it == trackers.end())
        {
            Q_ASSERT_CTX(false, name_, "Tracker not found")
        }
        it->second->autoAlloc(tag, thread_string, (2 - (int)instanceFactory::isTandemMode()));
    }
    void dealloc(const char* name, int tag)
    {
        std::string name_(name);
        auto it = trackers.find(name_);
        if (it == trackers.end())
        {
            Q_ASSERT_CTX(false, name_, "Tracker not found")
        }
        it->second->autoDealloc(tag, (2 - (int)instanceFactory::isTandemMode()));
    }
    void saveLastString(bool val)
    {
        for (auto it = trackers.begin(); it != trackers.end(); ++it)
        {
            it->second->saveLastString(val);
        }
    }

private:
    trackerCollection() {};
    std::map<std::string, std::shared_ptr<trackerBase>> trackers;

};
// this is a sample class suitable for using in a tracker
class simpleString {
public:
    simpleString(const std::string &info_) : info(info_) {}
    simpleString() : info("") {}
    std::string prt(void) {return(info);}
    inline bool operator==(const simpleString& rhs) const { return info == rhs.info; }
    void setInfo(const std::string &info_) {info = info_;}
private:
    std::string info;
};

class multiCycleTracker : public multiCycleBase
{
public:
    multiCycleTracker(int burst_size, std::string tracker_name)
     :  multiCycleBase(tracker_name, burst_size),
        tracker_(trackerCollection::GetInstance().getTracker(tracker_name.c_str()))
    {}
    uint8_t * getReadPtr(const int tag) override
    {
        return tracker_->getBackdoorPtr(tag);
    }
    uint8_t * getWritePtr(const int tag) override
    {
        return tracker_->getBackdoorPtr(tag);
    }
    uint32_t getReadBufferSize(const int tag) override
    {
        return tracker_->getLen(tag);
    }
    uint32_t getWriteBufferSize(const int tag) override
    {
        return tracker_->getLen(tag);
    }
    void initRead(int tag) override
    {
        m_read_cycles_total = (tracker_->getLen(tag) + m_burst_size - 1) / m_burst_size; // round up
        m_read_cycles_current = 0;
    }
    void copyReadData(const int tag, uint8_t *destination) override
    {
        uint8_t *source = tracker_->getBackdoorPtr(tag);
        Q_ASSERT_NODUMP(source != nullptr && destination != nullptr, "Null pointer in tracker copyReadData");
        memcpy(destination, source + (m_read_cycles_current * m_burst_size), m_burst_size);
    }
    void initWrite(int tag) override
    {
        m_write_tag = tag;
        if (list_mode)
        {
            // in list use case we rely on the list of sizes created by the interface user on the read side for the write
            Q_ASSERT(transaction_context.size() > 0, "Write attempting to perform transaction without setting transaction size. Make sure the read code issues push_context() prior to writer writing");
            m_write_tag = transaction_context.front();
            transaction_context.pop_front();
            Q_ASSERT(api_mode == false || tag == (int)m_write_tag, "Read and write sources do not agree on the tag for this transaction");
        }
        m_write_cycles_total = (tracker_->getLen(m_write_tag) + m_burst_size - 1) / m_burst_size; // round up
        m_write_cycles_current = 0;
    }
    void copyWriteData(const int tag, uint8_t *source) override
    {
        int tag_ = tag;
        // we need to detect if the caller(source) was non transactional and the reader was transactional
        // note that the caller of this function should always be non-transactional, but check for !api_mode just in case
        if (!api_mode && list_mode)
        {
            tag_ = m_write_tag;
        }
        uint8_t *destination = tracker_->getBackdoorPtr(tag_);
        Q_ASSERT_NODUMP(source != nullptr && destination != nullptr, "Null pointer in tracker copyWriteData");
        memcpy(destination + (m_write_cycles_current * m_burst_size), source, m_burst_size);
    }
    void set_write_context(uint32_t tag) override
    {
        Q_ASSERT((int)tag < tracker_->get_tracker_size(), "tag out of range");
        m_write_tag = tag;
    }
    int get_write_context(void) override { return m_write_tag;}
    void setListMode(void)
    {
        list_mode = true;
    }
private:
    std::shared_ptr<trackerBase> tracker_;
    uint32_t m_write_tag;
} ;

// must match DPI function prototypes
extern "C" {
    extern void tracker_alloc(const char* name, int tag, const char* thread_string);
    extern void tracker_dealloc(const char* name, int tag);
}

#endif //(TRACKER_H)
