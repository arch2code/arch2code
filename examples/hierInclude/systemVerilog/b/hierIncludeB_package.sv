// GENERATED_CODE_PARAM --context b/hierIncludeB.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package hierIncludeB_package;
// Generated Import package statement(s)
import hierIncludeTop_package::*;
import hierInclude_package::*;
import hierIncludeBInclude_package::*;

// types
typedef logic[9-1:0] bSizeT; //A type from an include sizing from constant B_ANOTHER_SIZE

// enums

// structures
typedef struct packed {
    bSizeT bAnother; //
} bSt;

endpackage : hierIncludeB_package
// GENERATED_CODE_END
