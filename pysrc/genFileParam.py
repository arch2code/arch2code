"""GENERATED_CODE_PARAM stamp of a generated file.

The PARAM line is a generated file's self-description: the arguments every
generated region in that file is rendered with, re-read from the file itself on
each `make gen` (parsed by textfileHelper.codeText.parseParam). This module owns
what that line SAYS for a context-mode artifact - its argument order and the
--mode token its file type carries - as opposed to textfileHelper, which owns
reading and rewriting the generated regions the line governs.

Two places produce the stamp and must agree exactly: the scaffold templates
(templates/fileGen/fileGen.py) write it when `make newmodule` creates the file,
and the context-param migration (pysrc/migrateProjectParam.py) rewrites it in
place on existing files. Both build it here, so a re-stamped line is
byte-identical to a fresh scaffold with no lock-step spelling to keep in sync.
"""

from pysrc.arch2codeHelper import printError, warningAndErrorReport


# Argument tail of a context-mode file's PARAM line. Order is owner first
# (resolveFileOwner reads --project directly), then the canonical yamlContext key
# the file renders, then the file type's --mode when it carries one.
def contextParamTail(owner, contextKey, mode=""):
    tail = f"--project={owner} --context={contextKey}"
    if mode:
        tail += f" --mode={mode}"
    return tail

# The --mode token a context-mode artifact carries, keyed by its INCLUDEFILES
# file key (<fileType>_<ext>). --mode selects the emission flavor the file
# regenerates with (structures.py codeMapping: absent -> 'model' SystemC types,
# 'fw' plain C++ firmware, 'module' C++20 module interface), so it is a property
# of the artifact KIND fixed by the template that scaffolds it, never a
# per-project choice. A re-stamp that dropped or changed the token would silently
# change the flavor the file regenerates as on the next `make gen`.
#
# Coverage is EXHAUSTIVE, not defaulted: every context file key reachable in
# INCLUDEFILES must appear, including the ones whose artifacts carry no --mode
# (mapped to ''). contextParamMode rejects an unknown key rather than omitting
# the token, so adding a context fileType to a fileMap fails loud until its mode
# is recorded here.
_CONTEXT_FILE_MODE = {
    'include_cppm': 'module',
    'package_sv': '',
    'includeFW_hdr': 'fw',
    'includeFW_src': 'fw',
}

def contextParamMode(fileKey):
    if fileKey not in _CONTEXT_FILE_MODE:
        printError(f"context file key '{fileKey}' has no entry in "
                   f"pysrc/genFileParam.py::_CONTEXT_FILE_MODE, so the "
                   f"GENERATED_CODE_PARAM --mode token its artifacts carry is "
                   f"unknown. Add it there with the --mode the fileGen template "
                   f"that scaffolds it emits (or '' when it carries none).")
        exit(warningAndErrorReport())
    return _CONTEXT_FILE_MODE[fileKey]
