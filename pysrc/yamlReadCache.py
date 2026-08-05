"""Process-scoped read-through byte cache for YAML files.

Every project build reads its projectFiles:/include: closure twice: the scan-all
pre-pass (projectScan, CSafeLoader) and readRaw's proper parse (existsLoad,
ruamel round-trip). The two parse differently, so the shared unit is raw file
bytes, not a parsed document. Both callers go through read(): the first read of
a path loads it from disk and caches the bytes, every later read of that path is
served from memory, so each file leaves disk once per build.

clear() marks the lifetime boundary. The cache lives only for the duration of
one closure read: projectCreate.__init__ clears at its start, so a build always
reflects current disk, and readRaw clears again once it has parsed the last
closure file, so the cached bytes are not held for the rest of the process. A
caller that RE-READS a path after the file changed on disk within that window
(e.g. a scanner unit test that edits a fixture and re-scans) must clear() first;
otherwise it is served the earlier bytes. Any future policy on what may be
cached belongs here, not in callers.
"""

import os

_cache = {}


def read(path):
    """Return the file's raw bytes, caching them on the first read (read-through).
    Keyed by canonical abspath so the scan pre-pass and the proper parse share
    one entry."""
    key = os.path.abspath(path)
    if key not in _cache:
        with open(path, 'rb') as fh:
            _cache[key] = fh.read()
    return _cache[key]


def clear():
    """Drop all entries (one closure-read lifetime)."""
    _cache.clear()
