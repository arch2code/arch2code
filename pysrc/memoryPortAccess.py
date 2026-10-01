"""Port access and register-port selection for memory types."""

# What each port of a memoryType allows, in A-then-B port order. A single-port
# memory's one port is keyed ''.
MEMORY_PORT_ACCESS = {
    'singlePort':  {'': 'rw'},
    'register':    {'': 'rw'},
    'dualPort':    {'A': 'rw', 'B': 'rw'},
    'portRportRW': {'A': 'ro', 'B': 'rw'},
    'portRWportW': {'A': 'rw', 'B': 'wo'},
    'portRportW':  {'A': 'ro', 'B': 'wo'},
}

def memoryRegisterPort(memoryType, regAccess):
    """Which memory port firmware reaches through the register handler.

    regAccess is False or the firmware access mode ('rw', 'ro', 'wo').
    Returns (regPort, portAccess): portAccess is the memoryType's row of
    MEMORY_PORT_ACCESS, and regPort is None when there is no firmware access
    or no port allows the mode. Among the ports that allow it, one whose
    access is exactly the mode wins, then port B.
    """
    portAccess = MEMORY_PORT_ACCESS[memoryType]
    if not regAccess:
        return None, portAccess
    allowed = [port for port, access in portAccess.items() if access in ('rw', regAccess)]
    exact = [port for port in allowed if portAccess[port] == regAccess]
    candidates = exact or allowed
    return (candidates[-1] if candidates else None), portAccess
