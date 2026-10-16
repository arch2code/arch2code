"""Temp-directory cleanup shared by the unit tests."""

import os
import shutil
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g


def close_db():
    # A deleted database file still open on NFS lingers as a .nfs placeholder
    # that keeps its directory from being removed until the connection closes.
    if g.db is not None:
        g.db.close()
        g.db = None


def remove_tree(path):
    close_db()
    shutil.rmtree(path)
