#ifndef REGADDRESSES_H
#define REGADDRESSES_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=includes --section=addresses 
//instance base addresses
#define BASE_ADDR_MIXED_TB             0x0
#define BASE_ADDR_U_MIXED              0x0
#define BASE_ADDR_UCPU                 0x0
#define BASE_ADDR_UBLOCKA              0x0
#define BASE_ADDR_UAPBDECODE           0x0
#define BASE_ADDR_UBLOCKC              0x0
#define BASE_ADDR_UBLOCKB              0x1000000
#define BASE_ADDR_UBLOCKD              0x0
#define BASE_ADDR_UBLOCKF0             0x200000
#define BASE_ADDR_UBLOCKF1             0x0
#define BASE_ADDR_UTHREECS             0x0
#define BASE_ADDR_UBLOCKC0             0x0
#define BASE_ADDR_UBLOCKC1             0x0
#define BASE_ADDR_UBLOCKC2             0x0
#define BASE_ADDR_UBLOCKBREGS          0x0
#define BASE_ADDR_UBLOCKAREGS          0x0
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=includes --section=regAddresses
//register addresses
#define REG_BLOCKB_RWD                      0xc0
#define REG_BLOCKB_ROBSIZE                  0xc8
#define REG_BLOCKA_ROA                      0x0
//memories base addresses
#define REG_BLOCKB_BLOCKBTABLE1             0x0
#define REG_BLOCKB_BLOCKBTABLEEXT           0x80
// GENERATED_CODE_END

#endif //REGADDRESSES_H

