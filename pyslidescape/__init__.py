from .version import __version__

import os
import warnings
import shutil
from importlib import resources as importlib_resources
import collections
import subprocess
import multiprocessing
import tempfile
import img2pdf
import pathlib

from xml.dom import minidom


def glob(path, pattern):
    """
    A glob which can find hidden files.
    """
    out = []
    for p in pathlib.Path(path).glob(pattern):
        out.append(str(p))
    return out


def inkscape_svg_export_layers(src, dst, hide, show):
    """
    Export selected layers of SVG in the file `src` to the file `dst`.

    :arg  str    src:  path of the source SVG file.
    :arg  str   dst:  path to export SVG file.
    :arg  list  hide:  layers to hide. each element is a string.
    :arg  list  show:  layers to show. each element is a string.

    """
    with open(src, "rt") as f:
        svg = minidom.parse(f)

    g_hide = []
    g_show = []
    for g in svg.getElementsByTagName("g"):
        if "inkscape:label" in g.attributes:
            label = g.attributes["inkscape:label"].value
            if label in hide:
                g.attributes["style"] = "display:none"
                g_hide.append(g)
            elif label in show:
                g.attributes["style"] = "display:inline"
                g_show.append(g)

    with open(dst, "wt") as f:
        f.write(svg.toxml())

    if False:
        print(
            "Hide {0} node(s);  Show {1} node(s).".format(
                len(g_hide), len(g_show)
            )
        )


def find_inkscape_labels_for_layers_in_inkscape_svg(path):
    inkscape_labels = []
    with open(path, "rt") as f:
        svg = minidom.parse(f)

    for g in svg.getElementsByTagName("g"):
        if "inkscape:label" in g.attributes:
            if "id" in g.attributes:
                if "layer" == g.attributes["id"].value:
                    inkscape_labels.append(
                        g.attributes["inkscape:label"].value
                    )
    return inkscape_labels


def inkscape_svg_roll_out_layers(
    layers_svg_path,
    layers_txt_path=None,
):
    path_wo_ext, ext = os.path.splitext(layers_svg_path)
    if layers_txt_path is None:
        layers_txt_path = path_wo_ext + ".txt"

    dirname = os.path.dirname(layers_svg_path)
    basename = os.path.basename(layers_svg_path)
    slide_id_str = str.partition(basename, ".")[0]

    all_labels = set(
        find_inkscape_labels_for_layers_in_inkscape_svg(path=layers_svg_path)
    )

    show_label_sets = []
    with open(layers_txt_path, "rt") as f:
        lines = f.read()
        for line in str.splitlines(lines):
            show_label_sets.append(set(str.split(line, ",")))

    for i in range(len(show_label_sets)):
        show_label_set = show_label_sets[i]
        hide_label_set = all_labels.difference(show_label_set)
        inkscape_svg_export_layers(
            src=layers_svg_path,
            dst=os.path.join(
                dirname, ".{:s}-{:04d}.svg".format(slide_id_str, i)
            ),
            show=show_label_set,
            hide=hide_label_set,
        )


def images_to_pdf(work_dir, out_path, continuous_slides):
    cache_dir = get_cache_dir(work_dir)

    list_of_image_paths = [
        os.path.join(
            cache_dir, "{:04d}.{:s}".format(sl["group_id"], sl["render_key"])
        )
        for sl in continuous_slides
    ]

    tmp_path = out_path + ".part"
    with open(tmp_path, "wb") as f:
        f.write(img2pdf.convert(list_of_image_paths))
    os.rename(tmp_path, out_path)


def inkscape_render(svg_path, out_path, background_opacity=0.0):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_image_png = os.path.join(tmp, "image.png")
        rc_ink = subprocess.call(
            [
                "inkscape",
                "--export-background-opacity={:f}".format(background_opacity),
                "--export-type={:s}".format("png"),
                "--export-filename={:s}".format(tmp_image_png),
                svg_path,
            ]
        )
        ext = os.path.splitext(out_path)
        if ext == ".png":
            os.rename(tmp_image_png, out_path)
        else:
            rc_con = subprocess.call(
                [
                    "convert",
                    tmp_image_png,
                    "-quality",
                    "98",
                    "-background",
                    "white",
                    "-alpha",
                    "remove",
                    out_path,
                ]
            )


def list_image_file_extensions():
    return [".png", ".jpg"]


def get_cache_dir(work_dir):
    return os.path.join(work_dir, ".cache")


def clean_work_dir(work_dir):
    group_dirs = list_slides_dirs(work_dir)
    for group_dir in group_dirs:
        layer_slide_paths = glob(path=group_dir, pattern=".*-*.svg")
        for layer_slide_path in layer_slide_paths:
            print("rm", layer_slide_path)
            os.remove(layer_slide_path)


def compile(work_dir, out_path, num_threads=1):
    cache_dir = get_cache_dir(work_dir)
    os.makedirs(cache_dir, exist_ok=True)
    pool = multiprocessing.Pool(num_threads)

    clean_work_dir(work_dir=work_dir)

    # roll out svgs with layers
    # -------------------------
    layers_jobs = inkscape_svg_roll_out_layers_make_jobs(work_dir=work_dir)
    _ = pool.map(inkscape_svg_roll_out_layers, layers_jobs)

    # render slides
    # -------------
    continuous_slides = query_group_and_slide_structure(work_dir)
    jobs = compile_make_jobs(
        work_dir=work_dir, continuous_slides=continuous_slides
    )

    _ = pool.map(compile_run_job, jobs)

    images_to_pdf(
        work_dir=work_dir,
        out_path=out_path,
        continuous_slides=continuous_slides,
    )


def compile_make_jobs(work_dir, continuous_slides):
    cache_dir = get_cache_dir(work_dir)

    jobs = []

    for cslide in continuous_slides:
        render_path = os.path.join(
            cache_dir,
            "{:04d}.{:s}".format(cslide["group_id"], cslide["render_key"]),
        )

        source_path = os.path.join(
            work_dir,
            "{:04d}.slides".format(cslide["group_id"]),
            cslide["basename"],
        )

        if os.path.exists(render_path):
            render_mtime = os.stat(render_path).st_mtime
            source_mtime = os.stat(source_path).st_mtime
            if source_mtime < render_mtime:
                continue

        job = {
            "render_path": render_path,
            "source_path": source_path,
            "background_opacity": 0.0,
        }
        jobs.append(job)
    return jobs


def compile_run_job(job):
    rc = inkscape_render(
        svg_path=job["source_path"],
        out_path=job["render_path"],
        background_opacity=job["background_opacity"],
    )
    return rc


def flatten_groups_and_slides(groups_and_slides):
    out = []
    i = 0
    for gkey in groups_and_slides:
        group = groups_and_slides[gkey]
        for skey in group:
            slide = {
                "group_id": gkey,
                "group_slide_id": skey,
                "continuous_id": i,
                "basename": group[skey]["basename"],
            }
            i += 1
            out.append(slide)
    return out


def query_group_and_slide_structure(work_dir):
    group_dirs = list_slides_dirs(work_dir)

    stru = []
    for group_dir in group_dirs:
        basename = os.path.basename(group_dir)
        group_id_str = str.partition(basename, ".")[0]
        group_id = int(group_id_str)

        items = list_files_which_could_be_rendered(group_dir)

        for item in items:
            item["group_id"] = group_id
            stru.append(item)

    return stru


def list_layers_svg_in_group_dir(group_dir):
    pp = glob(path=group_dir, pattern="*.layers.svg")
    pp = sorted(pp)
    out = []
    for p in pp:
        basename = os.path.basename(p)
        slide_id_str = str.partition(basename, ".")[0]
        if is_number(slide_id_str):
            out.append({"basename": basename, "slide_id": int(slide_id_str)})
    return out


def list_layers_svg_in_work_dir(work_dir):
    group_dirs = list_slides_dirs(work_dir)
    out = []
    for group_dir in group_dirs:
        basename = os.path.basename(group_dir)
        group_id_str = str.partition(basename, ".")[0]
        group_id = int(group_id_str)
        items = list_layers_svg_in_group_dir(group_dir)
        for item in items:
            item["group_id"] = group_id
            out.append(item)
    return out


def inkscape_svg_roll_out_layers_make_jobs(work_dir):
    layer_svgs = list_layers_svg_in_work_dir(work_dir=work_dir)
    jobs = []
    for layer_svg in layer_svgs:
        jobs.append(
            os.path.join(
                work_dir,
                "{:04d}.slides".format(layer_svg["group_id"]),
                "{:04d}.layers.svg".format(layer_svg["slide_id"]),
            )
        )
    return jobs


def list_files_which_could_be_rendered(work_dir):
    possible_extensions = list_image_file_extensions()
    possible_extensions += [".svg"]
    possible_extensions = set(possible_extensions)

    pp = glob(path=work_dir, pattern="*")
    pp = sorted(pp)
    out = []
    for path in pp:
        if not os.path.isfile(path):
            continue

        basename = os.path.basename(path)
        _, ext = os.path.splitext(basename)

        if ext is None:
            continue

        if str.lower(ext) not in possible_extensions:
            continue

        if "layers.svg" in basename:
            continue

        if basename.startswith("."):
            # might be a layer of a slide
            slide_and_layer_id_str = str.partition(basename[1:], ".")[0]
            slide_id_str_and_layer_id_str = str.split(
                slide_and_layer_id_str, "-"
            )
            if len(slide_id_str_and_layer_id_str) != 2:
                continue

            slide_id_str = slide_id_str_and_layer_id_str[0]
            layer_id_str = slide_id_str_and_layer_id_str[1]

            if is_number(slide_id_str) and is_number(layer_id_str):
                out.append(
                    {
                        "basename": basename,
                        "slide_id": int(slide_id_str),
                        "layer_id": int(layer_id_str),
                        "render_key": "{:04d}-{:04d}.jpg".format(
                            int(slide_id_str),
                            int(layer_id_str),
                        ),
                    }
                )

        else:
            # might be a regular slide
            slide_id_str = str.partition(basename, ".")[0]

            if is_number(slide_id_str):
                out.append(
                    {
                        "basename": basename,
                        "slide_id": int(slide_id_str),
                        "render_key": "{:04d}.jpg".format(int(slide_id_str)),
                    }
                )
    return out


def list_slides_dirs(work_dir):
    pp = glob(path=work_dir, pattern="*.slides")
    out = []
    for path in pp:
        if os.path.isdir(path):
            basename = os.path.basename(path)
            slides_id_str = str.partition(basename, ".")[0]
            if is_number(slides_id_str):
                out.append(path)
    out = sorted(out)
    return out


def is_number(txt):
    try:
        number = int(txt)
        return True
    except ValueError as err:
        pass
    return False


def write_template_slide(out_path):
    resource_dir = get_resources_dir()
    assert not os.path.exists(out_path), "Must not overwrite existing slide."
    shutil.copy(
        os.path.join(resource_dir, "slide_1920x1080.svg"), dst=out_path
    )


def get_resources_dir():
    return os.path.join(importlib_resources.files("pyslidescape"), "resources")
