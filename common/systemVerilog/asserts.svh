// Assertion macros
`ifndef ASSERTS_SVH
`define ASSERTS_SVH

// Assert with a fatal simulation stoppage
`define qAssertFatal(condition, comment) \
assert(condition) else $fatal(1, comment);

// Assert with a error, simulator will decide to stop or not
`define qAssertError(condition, comment) \
assert(condition) else $error(comment);

// Assert with a warning
`define qAssertWarning(condition, comment) \
assert(condition) else $warning(comment);

`endif 