//

#include "systemc.h"
#include <string>
#include <cstring>
#include <stdlib.h>
#include <unistd.h>
#include <limits.h>
#include <sys/wait.h>
#include <cstdio>

#include "instanceFactory.h"
#include "socketFactory.h"
#include "socketSync.h"
#include "socketTransport.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
#include "testController.h"
#include "axiSocketSocketCatalog.h"

namespace {

std::string resolveAxiSocketSlaveScriptPath()
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

    const std::string candidate = build_dir + "/../../axiSocketSlave.py";
    char resolved[PATH_MAX];
    if (realpath(candidate.c_str(), resolved) != nullptr) {
        return std::string(resolved);
    }
    return {};
}

} // namespace

// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=tbConfig

class axiSocketConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("axiSocket", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<axiSocketConfig>());}, is_default_testbench_v<axiSocketConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~axiSocketConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "axiSocketTestbench", "", "axiSocketSlave"); }
public:
// GENERATED_CODE_END

private:
    pid_t python_pid_ = -1;
    std::string ports_file_ = "";
    bool skip_sidecar_ = false;

public:
    bool createTestBench(void) override
    {
        instanceFactory::registerInstance("axiSocketSlave_tb.u_axiSocket", "socket");

        if (!axiSocketSocketCatalog::registerAll()) {
            return false;
        }

        if (setenv("PYSOCKET_PORTS", socketFactory::getPortString().c_str(), 1) != 0) {
            socketFactory::shutdownAll();
            return false;
        }

        if (ports_file_.empty() && getenv("PYSOCKET_PORTS_FILE") != nullptr) {
            ports_file_ = getenv("PYSOCKET_PORTS_FILE");
        }
        if (!ports_file_.empty()) {
            FILE *fp = std::fopen(ports_file_.c_str(), "w");
            if (fp != nullptr) {
                std::fprintf(fp, "%s\n", socketFactory::getPortString().c_str());
                std::fclose(fp);
            }
        }

        if (const char *skip_env = getenv("PYSOCKET_SKIP_PYTHON_SIDECAR")) {
            if (std::strcmp(skip_env, "true") == 0 || std::strcmp(skip_env, "1") == 0) {
                skip_sidecar_ = true;
            }
        }

        std::string sc_ports_file;
        if (!skip_sidecar_) {
            const std::string script_path = resolveAxiSocketSlaveScriptPath();
            if (script_path.empty()) {
                socketFactory::shutdownAll();
                return false;
            }
            pid_t sc_pid = getpid();
            sc_ports_file = "/tmp/axi_socket_slave_ports_" + std::to_string(sc_pid) + ".env";
            FILE *fp = std::fopen(sc_ports_file.c_str(), "w");
            if (fp != nullptr) {
                std::fprintf(fp, "%s", socketFactory::getPortString().c_str());
                std::fclose(fp);
            }
            pid_t pid = fork();
            if (pid == 0) {
                execlp("python3", "python3", script_path.c_str(), sc_ports_file.c_str(), nullptr);
                _exit(127);
            }
            if (pid < 0) {
                socketFactory::shutdownAll();
                return false;
            }
            python_pid_ = pid;
        }

        socketFactory::acceptAll();

        if (!sc_ports_file.empty()) {
            std::remove(sc_ports_file.c_str());
        }

        if (!axiSocketSocketCatalog::handshakeAll()) {
            socketFactory::shutdownAll();
            return false;
        }

        socketSyncStartRxThread();

        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "test_axird0",
            "test_axiwr0",
            "axiSocketSlaveTest",
        });

        (void)instanceFactory::createInstance("", "axiSocketSlave_tb", "axiSocketSlave_tb", "", "axiSocketSlave");
        return true;
    }

    void addProgramOptions(po::options_description &options) override
    {
        options.add_options()
            ("PYSOCKET_PORTS_FILE", po::value<std::string>(&ports_file_)->default_value(""), "File to write the ports to")
            ("PYSOCKET_SKIP_PYTHON_SIDECAR", po::bool_switch(&skip_sidecar_)->default_value(false), "Skip the Python sidecar");
    }

    void final(void) override
    {
        socketFactory::shutdownAll();
        if (python_pid_ > 0) {
            int status = 0;
            (void)waitpid(python_pid_, &status, 0);
            python_pid_ = -1;
        }
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        Q_ASSERT_CTX(testController::GetInstance().are_all_tests_complete(), "final", "Not all tests completed");
        errorCode::pass();
    }

};
axiSocketConfig::registerTestBenchConfig axiSocketConfig::registerTestBenchConfig_;
