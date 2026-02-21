// GENERATED_CODE_PARAM --context hierInclude.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package hierInclude_package;
// Generated Import package statement(s)
import hierIncludeNestedTop_package::*;
import hierIncludeTop_package::*;
localparam int unsigned ASIZE = 32'h0000_0007;  // The size of A
localparam int unsigned ASIZE2 = 32'h0000_000B;  // The size of A + included constant another size

// types
typedef logic[ASIZE-1:0] aSizeT; //type of width ASIZE
typedef logic[ASIZE2-1:0] aBiggerT; //yet another type
typedef logic[ANOTHER_SIZE-1:0] anotherSizeT; //A type with an included constant
typedef logic[YET_ANOTHER_SIZE-1:0] yetAnotherSizeT; //A type with a nested included constant

// enums

// structures
typedef struct packed {
    aSizeT variablea; //One bit of A
    aBiggerT [ASIZE2-1:0] variablea2; //Two bits of A
    anotherSizeT another; //
    yetAnotherSizeT yetAnother; //
} aSt;

typedef struct packed {
    anotherSizeT another; //
} anotherSt;

typedef struct packed {
    yetAnotherSizeT yetAnother; //
} yetAnotherSt;

endpackage : hierInclude_package
// GENERATED_CODE_END
