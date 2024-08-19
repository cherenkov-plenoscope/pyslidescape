from .version import __version__
from . import inkscape

import os
import shutil
from importlib import resources as importlib_resources
import multiprocessing
import img2pdf
import pathlib


def glob(path, pattern):
    """
    A glob which can find hidden files.
    """
    out = []
    for p in pathlib.Path(path).glob(pattern):
        out.append(str(p))
    return out


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
    _ = pool.map(inkscape.inkscape_svg_roll_out_layers, layers_jobs)

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
    rc = inkscape.inkscape_render(
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
