#ifndef REGRDWR_H
#define REGRDWR_H

void regWrite32(uint64_t address, uint32_t value);
uint32_t regRead32(uint64_t address);
void regWrite64(uint64_t address, uint64_t value);
uint64_t regRead64(uint64_t address);

#endif // REGRDWR_H