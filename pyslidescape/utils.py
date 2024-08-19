import importlib.resources
import os
import pathlib


def get_resources_dir():
    return os.path.join(importlib.resources.files("pyslidescape"), "resources")


def glob(path, pattern):
    """
    A glob which can find hidden files.
    """
    out = []
    for p in pathlib.Path(path).glob(pattern):
        out.append(str(p))
    return out
