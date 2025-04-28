`ifndef SYNCHLOCK_DPI_SV
//`define SYNCHLOCK_DPI_SV /* This is intentionaly commented out */

import "DPI-C" function int is_tandem ();
import "DPI-C" function void mutex_lock (string hierarchy, string name, string threadName, longint value);
import "DPI-C" function void mutex_unlock (string hierarchy, string name, string threadName);
import "DPI-C" function void synch_lock_arb(string hierarchy, string name, longint value);
import "DPI-C" function void row_lock(string hierarchy, string name, string thread_name, longint magicNumber, longint row);
import "DPI-C" function void push_arb (string hierarchy, string name, string threadName, longint value);

function int unsigned fnv1a_hash(input byte unsigned data[]);
    int unsigned hash;
    hash = 32'h811C9DC5;
    foreach(data[i]) begin
      hash ^= int'(data[i]);
      hash *= 32'h01000193;
    end
    return hash;
endfunction

// Macro replaces the streaming operator capability on dynamic arrays not well supported with verilator
// Equivalent to
//    int unsigned hashvar = fnv1a_hash({>>8{datavar}});
// Important note : bit slicing may exceed size of datavar, when size not byte aligned,
//     but verilator does not seem to generate error when encountering this case
`define HASH_VAR(datavar, hashvar) \
    begin \
        byte unsigned _data []; \
        _data = new[($size(datavar)+7)/8]; \
        foreach(_data[i]) _data[i] = datavar[8*i+:8]; \
        hashvar = fnv1a_hash(_data); \
    end

`endif // SYNCHLOCK_DPI_SV
