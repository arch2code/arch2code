#ifndef REGADDRESSES_H
#define REGADDRESSES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=includes --section=addresses 
//instance base addresses
#define BASE_ADDR_UTOP                 0x0
#define BASE_ADDR_UCPU                 0x0
#define BASE_ADDR_UAPBDECODE           0x0
#define BASE_ADDR_USOMERAPPER          0x0
#define BASE_ADDR_UBLOCKA              0x0
#define BASE_ADDR_UBLOCKB              0x1000000
#define BASE_ADDR_UBLOCKAREGS          0x0
#define BASE_ADDR_UBLOCKBREGS          0x0
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=includes --section=regAddresses
//register addresses
#define REG_BLOCKB_RWUN0B                   0x200
#define REG_BLOCKB_ROB                      0x208
#define REG_BLOCKA_ROA                      0x200
#define REG_BLOCKA_RWUN0A                   0x208
#define REG_BLOCKA_ROUN0A                   0x210
#define REG_BLOCKA_EXTA                     0x218
//memories base addresses
#define REG_BLOCKA_BLOCKATABLE0             0x0
#define REG_BLOCKA_BLOCKATABLE1             0x100
#define REG_BLOCKB_BLOCKBTABLE              0x0
// GENERATED_CODE_END

#endif //REGADDRESSES_H

