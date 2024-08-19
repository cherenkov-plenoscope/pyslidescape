from .version import __version__
from . import inkscape
from . import utils

import os
import shutil


def init(work_dir):
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.join(work_dir, "resources"), exist_ok=True)

    _fname = "max_planck_institute_for_nuclearphysics.svg"
    shutil.copy(
        os.path.join(get_resources_dir(), _fname),
        os.path.join(work_dir, "resources", _fname)
    )

    init_slide_dir(path=os.path.join(work_dir, "first.slide"))
    _fname = "work_in_progress_placeholder.svg"
    shutil.copy(
        os.path.join(get_resources_dir(), _fname),
        os.path.join(work_dir, "first.slide", "resources", _fname)
    )

    init_slide_dir(path=os.path.join(work_dir, "second.slide"))
    _fname = "work_in_progress_placeholder.svg"
    shutil.copy(
        os.path.join(get_resources_dir(), _fname),
        os.path.join(work_dir, "first.slide", "resources", _fname)
    )

    slide_order_filename = "slides.txt"
    with open(os.path.join(work_dir, slide_order_filename), "wt") as f:
        f.write("first.slide\n")
        f.write("second.slide\n")


def init_slide_dir(path):
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "resources"), exist_ok=True)
    slide_path = os.path.join(path, "layers.svg")

    with open(slide_path, "wt") as f:
        f.write(inkscape.init_slide_svg(1920, 1080))

    layer_order_path = os.path.join(path, "layers.txt")
    with open(layer_order_path, "wt") as f:
        f.write("one\n")
        f.write("two\n")