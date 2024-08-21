import importlib.resources
import os
import pathlib
import multiprocessing
import shutil
import json


class SerialPool:
    def __init__(self):
        pass

    def map(self, func, iterable):
        return [func(item) for item in iterable]


def init_multiprocessing_pool(num_threads=1):
    """
    This is only to ease debugging.
    Do not spawn an additional thread when num_threads == 1, but do the compute
    in the already existing thread.
    """
    assert num_threads > 0
    if num_threads == 1:
        return SerialPool()
    else:
        return multiprocessing.Pool(num_threads)


def init_multiprocessing_pool_if_None(pool):
    if pool is None:
        total_count = multiprocessing.cpu_count()
        count = max([1, total_count // 4])
        return multiprocessing_pool(count)
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


def write_dict_to_json(path, d):
    tmp_path = path + ".part"
    with open(tmp_path, "wt") as f:
        f.write(json.dumps(d, indent=4))
    os.rename(tmp_path, path)


def read_json_to_dict(path):
    with open(path, "rt") as f:
        return json.loads(f.read())
