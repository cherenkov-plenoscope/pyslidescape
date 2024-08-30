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
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        for src_path in glob(src, "*"):
            src_relpath = os.path.relpath(src_path, src)
            dst_path = os.path.join(dst, src_relpath)

            if os.path.isdir(src_path):
                _update = copytree_lazy(
                    src=src_path, dst=dst_path, verbose=verbose
                )
            else:
                _update = copy_lazy(
                    src=src_path, dst=dst_path, verbose=verbose
                )

            if _update:
                updates = True
        return updates
    else:
        return copy_lazy(src=src, dst=dst, verbose=verbose)


def copy_lazy(src, dst, verbose=False):
    need_to_copy = False
    if not os.path.exists(dst):
        need_to_copy = True
    else:
        src_mtime = mtime(src)
        dst_mtime = mtime(dst)
        if dst_mtime < src_mtime:
            need_to_copy = True

    if need_to_copy:
        if verbose:
            print(f"copy {src:s} to {dst:s}")
        shutil.copy(src, dst)

    return need_to_copy


def read_lines_from_textfile(path):
    with open(path, "rt") as f:
        lines = f.readlines()
    lines = [str.strip(line) for line in lines]
    return lines


def laods_layers_txt(s):
    layers = {}
    current_layer = None
    for line in str.splitlines(s):
        if len(line) > 0:
            first_char = line[0]
            if str.isspace(first_char):
                assert (
                    current_layer is not None
                ), "Expected layer before speech."
                layers[current_layer].append(str.strip(line))
            else:
                current_layer = line
                layers[current_layer] = []
    return layers


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
