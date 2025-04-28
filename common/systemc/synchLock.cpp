// copyright QiStor 2022
#ifndef A2CPRO
#include "systemc.h"

#include <string>
#include "logging.h"
#include "synchLock.h"
#include "hwMemory.h"

std::string systemC_safe_string(const std::string &str)
{
    std::string ret(str);
    std::replace(ret.begin(), ret.end(), '.', '_'); // convert . to _ for systemC names
    return ret;
}

int is_tandem() {  
    return false;
}

void mutex_lock(const char* hierarchy, const char* name, const char* thread_name, long long syncValue) {
    return;
}

void mutex_unlock(const char* hierarchy, const char* name, const char* thread_name) {
    return;
}

void synch_lock_arb(const char* hierarchy, const char* name, long long value)
{
    return;
}
void push_arb(const char* hierarchy, const char* name, const char* thread_name, long long syncValue)
{
    return;
}
void row_lock(const char* hierarchy, const char* name, const char* thread_name, long long magicNumber, long long row) {
    return;
}

uint32_t fnv1a_hash(const uint8_t* data, size_t length) {
    return 0;
}
#endif //A2CPRO