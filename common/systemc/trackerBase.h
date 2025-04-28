#ifndef TRACKERBASE_H
#define TRACKERBASE_H
#include <string>

//base class with trivial implementations to make overloading optional
class trackerBase 
{
public:
    virtual std::string prt(const int tag, bool noAssert=false) { return("");};
    virtual std::string prt(const int tag, const std::string &s){ return(s);};
    virtual std::string prt(const int tag, const std::string &s, const std::string &lastPrefix){ return(s);};
    virtual std::string getString(const int tag) { return("");};
    virtual std::string getString(const int tag, const std::string &s) { return(s);};
    virtual std::string getLastString(const int tag) { return("");};
    virtual void saveLastString(const bool val) = 0;
    virtual uint64_t getLen(const int tag) { return (-1);};
    virtual void setLen(const int tag, const uint64_t len) {};
    virtual uint8_t * getBackdoorPtr(const int tag) { return(nullptr);};
    virtual uint8_t * initGetBackdoorPtr(const int tag) { return(nullptr);};
    virtual void setBackdoorPtr(const int tag, uint8_t * ptr) = 0;
    virtual void initBackdoorPtr(const int tag, uint8_t * ptr) = 0;
    virtual void initBackdoorBuffer(const int tag, uint32_t size) = 0;
    virtual void autoDealloc(const int tag, const int useCount=2) = 0; // function to allow conditional deallocation
    virtual void autoAlloc(const int tag, const std::string &trackerString, const int useCount=2) = 0; // function to allow conditional allocation
    virtual void dump(void) {};
    virtual int get_tracker_size(void) const = 0;
    virtual bool is_valid(const int tag) const = 0; // this function should only be used for debug purposes
    virtual ~trackerBase() {};
};



#endif //(TRACKERBASE_H)
