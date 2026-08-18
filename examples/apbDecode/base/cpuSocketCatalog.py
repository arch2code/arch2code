# GENERATED_CODE_PARAM --block=cpu
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'apbReg': {
        "port": 'apbReg',
        "name": 'cpu.apbReg',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'cpu.apbReg_obs',
    },
}

LISTEN_NAMES = (
    'cpu.apbReg',
    'cpu.apbReg_obs',
)
SYNC_NAMES = (
    'pysocket_sync',
)

def required_names():
    return list(LISTEN_NAMES) + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port):
    return CATALOG[port]["name"]

def observe_name_for_port(port):
    return CATALOG[port]["observeName"]

# GENERATED_CODE_END
