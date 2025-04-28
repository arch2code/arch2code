#ifndef MIXEDENCODERS_H
#define MIXEDENCODERS_H

#include "mixedIncludes.h"
#include "encoderBase.h"

// GENERATED_CODE_PARAM --context=mixed.yaml
// GENERATED_CODE_BEGIN --template=encoder
class encoderOpcodeEnA : public encoderBase< opcodeTagT, opcodeEnumT >
{
public:
    encoderOpcodeEnA() : encoderBase< opcodeTagT, opcodeEnumT >(
        {   // encVal    encMask     max       hex width       name
            { 0x000, 0x1c0, (uint64_t)1<<DWORD_LOG2, ((DWORD_LOG2 + 3) >> 2), "read", "read"},
            { 0x040, 0x1c0, (uint64_t)1<<DWORD_LOG2, ((DWORD_LOG2 + 3) >> 2), "write", "write"},
            { 0x080, 0x1c0, (uint64_t)1<<DWORD_LOG2, ((DWORD_LOG2 + 3) >> 2), "wait", "wait"},
            { 0x0c0, 0x1c0, (uint64_t)1<<DWORD_LOG2, ((DWORD_LOG2 + 3) >> 2), "evict", "evict"},
            { 0x100, 0x1fe, (uint64_t)1<<1, ((1 + 3) >> 2), "trim", "trim"},
        }, 9, 0x101, true) {}
};

// GENERATED_CODE_END


#endif //MIXEDENCODERS_H
