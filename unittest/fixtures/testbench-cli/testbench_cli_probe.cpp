// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Runs the shipped sc_main (common/scmain/main.cpp) with testbench paramProbe,
// whose config registers --param key foo with default and maximum 3, and key
// zero with 0, which the command line cannot set. The testbench prints the
// value of foo it sees once simulation starts, then stops.

#include "main.cpp"
#include <memory>
#include <string>

struct paramHarness : sc_module
{
    SC_HAS_PROCESS( paramHarness );
    explicit paramHarness( sc_module_name n ) : sc_module( n ) { SC_THREAD( report ); }

    void report()
    {
        wait( 200, SC_NS );
        std::cout << "foo=" << testBenchConfigBase::getParam( "foo" ) << "\n";
        sc_stop();
    }
};

struct paramProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<paramHarness> harness;
    paramProbeConfig() { addParam( { { "foo", 3 }, { "zero", 0 } } ); }
    bool createTestBench( void ) override
    {
        harness = std::make_unique<paramHarness>( "harness" );
        return true;
    }
};

static int registerParamProbeConfig()
{
    testBenchConfigFactory::registerTestBenchConfig( "paramProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<paramProbeConfig>(); } );
    return 0;
}
[[maybe_unused]] static int paramProbeConfigRegistered = registerParamProbeConfig();
