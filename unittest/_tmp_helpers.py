"""Temp-directory cleanup shared by the unit tests."""

import os
import shutil
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g


def remove_tree(path):
    # An open database file on NFS leaves a .nfs placeholder that keeps its
    # directory from being removed, so the last projectOpen connection is closed first.
    if g.db is not None:
        g.db.close()
        g.db = None
    shutil.rmtree(path)
