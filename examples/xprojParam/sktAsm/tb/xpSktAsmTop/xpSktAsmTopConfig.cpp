// 

// GENERATED_CODE_PARAM --block=xpSktAsmTop
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
#include "systemc.h"
#include <cstdio>
#include <limits.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

#include "socketFactory.h"
#include "socketTransport.h"
#include "xpSktLeafSocketCatalog.h"

namespace {

// Instance path of the socket shell; xpSktAsm.py spells the same path.
constexpr const char *LEAF_INSTANCE = "xpSktAsmTop.uLeaf";

// The sidecar sits at the project root, two levels above rundir/build/<binary>.
std::string resolveSidecarPath()
{
    char self_path[PATH_MAX];
    const ssize_t n = readlink("/proc/self/exe", self_path, sizeof(self_path) - 1);
    if (n < 0) {
        return {};
    }
    self_path[n] = '\0';
    std::string build_dir(self_path);
    build_dir.resize(build_dir.find_last_of('/'));
    const std::string candidate = build_dir + "/../../xpSktAsm.py";
    char resolved[PATH_MAX];
    if (realpath(candidate.c_str(), resolved) == nullptr) {
        return {};
    }
    return std::string(resolved);
}

} // namespace
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class xpSktAsmTopConfig : public testBenchConfigBase
{
public:
    virtual ~xpSktAsmTopConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "xpSktAsmTopTestbench", "", "xpSktAsm"); }
public:
// GENERATED_CODE_END

private:
    pid_t python_pid_ = -1;

public:
    // uLeaf runs as its socket shell, so the leaf the factory builds is
    // xpSktLeafSocket at the Config only this project declares.
    bool createTestBench(void) override
    {
        instanceFactory::registerInstance(LEAF_INSTANCE, "socket");

        if (!xpSktLeafSocketCatalog::registerInstance(LEAF_INSTANCE)) {
            return false;
        }
        if (xpSktLeafSocketCatalog::uses_lockstep &&
            socketFactory::registerInterface(PYSOCKET_SYNC_IFC) == 0) {
            socketFactory::shutdownAll();
            return false;
        }
        const std::string script_path = resolveSidecarPath();
        if (script_path.empty()) {
            socketFactory::shutdownAll();
            return false;
        }
        const std::string ports_file = "/tmp/xp_skt_asm_ports_" + std::to_string(getpid()) + ".env";
        FILE *fp = std::fopen(ports_file.c_str(), "w");
        if (fp == nullptr) {
            socketFactory::shutdownAll();
            return false;
        }
        std::fprintf(fp, "%s", socketFactory::getPortString().c_str());
        std::fclose(fp);
        const pid_t pid = fork();
        if (pid == 0) {
            execlp("python3", "python3", script_path.c_str(), ports_file.c_str(), nullptr);
            _exit(127);
        }
        if (pid < 0) {
            socketFactory::shutdownAll();
            return false;
        }
        python_pid_ = pid;

        socketFactory::acceptAll();
        std::remove(ports_file.c_str());
        if (!socketFactory::handshakeAll()) {
            socketFactory::shutdownAll();
            return false;
        }

        (void)instanceFactory::createInstance("", "xpSktAsmTop", "xpSktAsmTop", "", "xpSktAsm");
        return true;
    }

    void final(void) override
    {
        socketFactory::shutdownAll();
        if (python_pid_ > 0) {
            int status = 0;
            (void)waitpid(python_pid_, &status, 0);
            Q_ASSERT_CTX(WIFEXITED(status) && WEXITSTATUS(status) == 0, "final", "Python sidecar failed");
            python_pid_ = -1;
        }
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration
// === Testbench config registration (xpSktAsmTopConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_xpSktAsmTopConfig() {
    testBenchConfigFactory::registerTestBenchConfig("xpSktAsmTop", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<xpSktAsmTopConfig>());}, is_default_testbench_v<xpSktAsmTopConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpSktAsmTopConfig_registered = (register_xpSktAsmTopConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
