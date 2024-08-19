import importlib.resources
import os
import pathlib
import multiprocessing
import shutil


def init_multiprocessing_pool_if_None(pool):
    if pool is None:
        total_count = multiprocessing.cpu_count()
        count = max([1, total_count // 4])
        return multiprocessing.Pool(count)
    else:
        return pool


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


def copytree_lazy(src, dst, verbose=False):
    updates = False

    for src_path in glob(src, "*"):
        src_relpath = os.path.relpath(src_path, src)
        dst_path = os.path.join(dst, src_relpath)

        need_to_copy = False
        if not os.path.exists(dst_path):
            need_to_copy = True
        else:
            src_mtime = mtime(src_path)
            dst_mtime = mtime(dst_path)
            if dst_mtime < src_mtime:
                need_to_copy = True

        if need_to_copy:
            updates = True
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            if verbose:
                print(f"copy {src_path:s} to {dst_path:s}")
            shutil.copy(src_path, dst_path)

    return updates


def read_lines_from_textfile(path):
    with open(path, "rt") as f:
        lines = f.readlines()
    lines = [str.strip(line) for line in lines]
    return lines


def mtime(path):
    return os.stat(path).st_mtime


def youngest_mtime_in_dir(path):
    paths = glob(path=path, pattern="*")
    mtimes = [mtime(p) for p in paths]
    if len(mtimes) == 0:
        return None
    else:
        return max(mtimes)
