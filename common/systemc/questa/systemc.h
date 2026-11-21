// Questa only (USE_QUESTA puts this directory first on the include path).
// Questa's SystemC defines the static member ptrarray<T*>::m_default_init_size
// out of class. Clang instantiates it at the end of every C++20 module unit
// whose global module fragment includes systemc.h and rejects it there as
// attached to the module. Declaring the specializations Questa's inline code
// uses `extern template` here, after its systemc.h, leaves their definitions to
// questa_sc_main.cpp, which sccom compiles outside any module.
#ifndef A2C_QUESTA_SYSTEMC_H
#define A2C_QUESTA_SYSTEMC_H
// #include_next is a GNU extension, which -Wpedantic reports.
#pragma GCC system_header
#include_next <systemc.h>
#ifdef MTI_SYSTEMC
#define A2C_QUESTA_PTRARRAY(T) extern template class ptrarray<T>;
#include "a2c_questa_ptrarray.def"
#undef A2C_QUESTA_PTRARRAY
#endif
#endif
