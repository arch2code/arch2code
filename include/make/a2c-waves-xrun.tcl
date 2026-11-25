# Sourced by the run script of a WAVES=1 Xcelium snapshot: probes every
# signal under WAVES_SCOPE, by default sc_main, which holds the whole
# testbench, into waves.shm in the directory the run started from, then runs
# to the end. The simulation's exit status is kept.
set scope sc_main
if {[info exists env(WAVES_SCOPE)]} { set scope $env(WAVES_SCOPE) }
puts "A2C_WAVES: probing $scope into $env(A2C_WAVES_DIR)/waves.shm"
database -open a2c_waves -shm -into $env(A2C_WAVES_DIR)/waves.shm -default
probe -create -database a2c_waves -all -depth all $scope
run
exit
