`ifndef TRACKER_DPI_SV
//`define TRACKER_DPI_SV /* This is intentionaly commented out */

import "DPI-C" function void tracker_alloc(string name, int tag, string trackerString);
import "DPI-C" function void tracker_dealloc(string name, int tag);

`endif // TRACKER_DPI_SV
