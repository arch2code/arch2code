#ifndef ADDRESSBASE_H
#define ADDRESSBASE_H
#include <cstdint>

constexpr int nextPowerOf2min4(int n)
{
    n--;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    n++;
    n = (n < 4) ? 4 : n;
    return n;
}

class addressBase {
public:
    addressBase() {};
    virtual void cpu_write(uint64_t address, uint32_t val) = 0;  //virtual methods to be overridden in template
    virtual uint32_t cpu_read(uint64_t address) = 0;
private:
};



#endif //(ADDRESSBASE_H)
