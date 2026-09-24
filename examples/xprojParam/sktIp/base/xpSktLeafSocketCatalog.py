# GENERATED_CODE_PARAM --block=xpSktLeaf
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'out': {
        "port": 'out',
        "nameSuffix": '.out',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
}

LISTEN_SUFFIXES = (
    '.out',
)
SYNC_NAMES = ()

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
