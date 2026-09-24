# GENERATED_CODE_PARAM --block=axiSocket
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'axiRd0': {
        "port": 'axiRd0',
        "nameSuffix": '.axiRd0',
        "interfaceType": 'axi_read',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": '.axiRd0_obs',
    },
    'axiWr0': {
        "port": 'axiWr0',
        "nameSuffix": '.axiWr0',
        "interfaceType": 'axi_write',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": '.axiWr0_obs',
    },
}

LISTEN_SUFFIXES = (
    '.axiRd0',
    '.axiWr0',
    '.axiRd0_obs',
    '.axiWr0_obs',
)
SYNC_NAMES = (
    'pysocket_sync',
)

def required_names(instance):
    return [instance + suffix for suffix in LISTEN_SUFFIXES] + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port, instance):
    return instance + CATALOG[port]["nameSuffix"]

def observe_name_for_port(port, instance):
    suffix = CATALOG[port]["observeSuffix"]
    return None if suffix is None else instance + suffix

# GENERATED_CODE_END
