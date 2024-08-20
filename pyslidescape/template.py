from . import utils
from . import inkscape

import os
import shutil


def init(work_dir):
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.join(work_dir, "resources"), exist_ok=True)

    _fname = "max_planck_institute_for_nuclearphysics.svg"
    shutil.copy(
        os.path.join(utils.get_resources_dir(), _fname),
        os.path.join(work_dir, "resources", _fname),
    )

    slides_dir = os.path.join(work_dir, "slides")
    os.makedirs(slides_dir, exist_ok=True)

    init_slide_dir(path=os.path.join(slides_dir, "first"))
    _fname = "work_in_progress_placeholder.svg"
    shutil.copy(
        os.path.join(utils.get_resources_dir(), _fname),
        os.path.join(slides_dir, "first", "resources", _fname),
    )

    init_slide_dir(path=os.path.join(slides_dir, "second"))
    _fname = "work_in_progress_placeholder.svg"
    shutil.copy(
        os.path.join(utils.get_resources_dir(), _fname),
        os.path.join(slides_dir, "second", "resources", _fname),
    )

    slides_txt_path = os.path.join(work_dir, "slides.txt")
    with open(slides_txt_path, "wt") as f:
        f.write("first\n")
        f.write("second\n")


def init_slide_dir(path):
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "resources"), exist_ok=True)
    slide_path = os.path.join(path, "layers.svg")

    with open(slide_path, "wt") as f:
        f.write(inkscape.init_slide_svg(1920, 1080))

    layer_order_path = os.path.join(path, "layers.txt")
    with open(layer_order_path, "wt") as f:
        f.write("one\n")
        f.write("one,two\n")
