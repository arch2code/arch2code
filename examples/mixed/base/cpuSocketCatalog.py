# GENERATED_CODE_PARAM --block=cpu
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'cpu_main': {
        "port": 'cpu_main',
        "name": 'cpu.cpu_main',
        "interfaceType": 'apb',
        "direction": 'src',
        "role": 'drive',
        "observeName": 'cpu.cpu_main_obs',
    },
}

LISTEN_NAMES = (
    'cpu.cpu_main',
    'cpu.cpu_main_obs',
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
