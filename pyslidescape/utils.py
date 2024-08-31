import importlib.resources
import os
import pathlib
import multiprocessing
import shutil
import json
from . import layers_txt


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


def init_todo_if_None(todo, work_dir):
    if todo is None:
        return init_todo(work_dir=work_dir)
    else:
        return todo


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


def write_lines_to_textfile(path, lines):
    tmp_path = path + ".part"
    with open(tmp_path, "wt") as f:
        for line in lines:
            f.write(line)
            f.write("\n")
    os.rename(tmp_path, path)


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


def init_todo(work_dir):
    """
    status_of_what_needs_to_be_done
    """
    slides_txt_path = os.path.join(work_dir, "slides.txt")
    slides = read_lines_from_textfile(path=slides_txt_path)
    sts = []
    for slide in slides:
        slide_dir = os.path.join(work_dir, "slides", slide)
        sls = {}
        sls["slide"] = slide
        with open(os.path.join(slide_dir, "layers.txt"), "rt") as f:
            layers = layers_txt.loads(f.read())

        show_layer_sets = [
            layers_txt.split_show_layers_set(layer) for layer in layers
        ]
        sls["show_layer_sets"] = show_layer_sets
        sls["notes"] = {}
        for layer in layers:
            sls["notes"][layer] = layers[layer]
        sts.append(sls)
    return sts
