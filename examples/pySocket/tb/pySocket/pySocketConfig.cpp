// 

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "pySocketIpc.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "testController.h"

// Absolute path to pySocket.py: do not rely on getcwd() — runs may start from FIPS/rundir or .../pySocket/rundir.
std::string resolvePySocketScriptPath()
{
    if (const char *env = getenv("PYSOCKET_PY_SCRIPT")) {
        if (env[0] != '\0') {
            char resolved[PATH_MAX];
            if (realpath(env, resolved) != nullptr) {
                return std::string(resolved);
            }
            return std::string(env);
        }
    }

    char self_path[PATH_MAX];
    const ssize_t n = readlink("/proc/self/exe", self_path, sizeof(self_path) - 1);
    if (n < 0) {
        return {};
    }
    self_path[n] = '\0';
    std::string build_dir(self_path);
    const auto slash = build_dir.find_last_of('/');
    if (slash == std::string::npos) {
        return {};
    }
    build_dir.resize(slash);

    const std::string candidate = build_dir + "/../../pySocket.py";
    char resolved[PATH_MAX];
    if (realpath(candidate.c_str(), resolved) != nullptr) {
        return std::string(resolved);
    }
    return {};
}

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=tbConfig

class pySocketConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("pySocket", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<pySocketConfig>());}, is_default_testbench_v<pySocketConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~pySocketConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        //create hierarchy
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "pySocket_tb", "pySocket_tb", "");

        std::uint16_t port_py2sc_request = 0;
        std::uint16_t port_py2sc_response = 0;
        std::uint16_t port_sc2py_request = 0;
        std::uint16_t port_sc2py_response = 0;
        if (!pySocketIpc::start_servers(port_py2sc_request, port_py2sc_response, port_sc2py_request, port_sc2py_response)) {
            return false;
        }
        if (setenv("PYSOCKET_PY2SC_REQUEST_PORT", std::to_string(port_py2sc_request).c_str(), 1) != 0) {
            pySocketIpc::close_channels();
            return false;
        }
        if (setenv("PYSOCKET_PY2SC_RESPONSE_PORT", std::to_string(port_py2sc_response).c_str(), 1) != 0) {
            pySocketIpc::close_channels();
            return false;
        }
        if (setenv("PYSOCKET_SC2PY_REQUEST_PORT", std::to_string(port_sc2py_request).c_str(), 1) != 0) {
            pySocketIpc::close_channels();
            return false;
        }
        if (setenv("PYSOCKET_SC2PY_RESPONSE_PORT", std::to_string(port_sc2py_response).c_str(), 1) != 0) {
            pySocketIpc::close_channels();
            return false;
        }

        pid_t pid = fork();
        if (pid == 0) {
            const std::string script_path = resolvePySocketScriptPath();
            if (script_path.empty()) {
                _exit(126);
            }
            execlp("python3", "python3", script_path.c_str(), NULL);
            _exit(127);
        }
        if (pid < 0) {
            pySocketIpc::close_channels();
            return false;
        }

        if (!pySocketIpc::accept_clients()) {
            pySocketIpc::close_channels();
            return false;
        }

        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "python2SystemCTest",
            "systemC2PythonTest"
        });

        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
pySocketConfig::registerTestBenchConfig pySocketConfig::registerTestBenchConfig_; //register the testBench with the factory
