from .version import __version__
from . import inkscape
from . import utils
from . import portable_document_format
from . import template
from . import latex

import os
import shutil
import warnings
import multiprocessing


def add_slide(work_dir, slide_name, slide_format=None):
    if slide_format is None:
        presentation_config = utils.read_json_to_dict(
            os.path.join(work_dir, ".config.json")
        )
        slide_format = presentation_config["slide_format"]

    slide_dir = os.path.join(work_dir, "slides", slide_name)
    template.init_slide_dir(path=slide_dir, slide_format=slide_format)


def status_of_what_needs_to_be_done(work_dir):
    slides_txt_path = os.path.join(work_dir, "slides.txt")
    slides = utils.read_lines_from_textfile(path=slides_txt_path)
    sts = []
    for slide in slides:
        slide_dir = os.path.join(work_dir, "slides", slide)
        sls = {}
        sls["slide"] = slide
        layers_txt_path = os.path.join(slide_dir, "layers.txt")
        lines = utils.read_lines_from_textfile(path=layers_txt_path)
        show_layer_sets = [str.split(line, ",") for line in lines]
        sls["show_layer_sets"] = show_layer_sets
        sts.append(sls)
    return sts


def compile(work_dir, out_path=None, pool=None, verbose=True):
    """
    pdf
        resources
        slides
            slide_A
                resources
                layers_to_be_shown
            slide_B
                ...
    """
    if out_path is None:
        out_path = os.path.join(work_dir, "slides.pdf")
    pool = utils.init_multiprocessing_pool_if_None(pool=pool)

    build_dir = os.path.join(work_dir, ".build")
    os.makedirs(build_dir, exist_ok=True)

    todo = status_of_what_needs_to_be_done(work_dir=work_dir)

    # latex snippets and slides
    # -------------------------
    update_latex_slides_and_snippets(
        work_dir=work_dir, todo=todo, pool=pool, verbose=verbose
    )

    # resources
    # ---------
    resource_updates = {}
    resource_updates["resources"] = utils.copytree_lazy(
        src=os.path.join(work_dir, "resources"),
        dst=os.path.join(build_dir, "resources"),
        verbose=verbose,
    )

    resource_updates["slides"] = {}
    for i in range(len(todo)):
        slide = todo[i]["slide"]

        resource_updates["slides"][slide] = utils.copytree_lazy(
            src=os.path.join(work_dir, "slides", slide, "resources"),
            dst=os.path.join(build_dir, "slides", slide, "resources"),
            verbose=verbose,
        )

    # svg roll out
    # ------------
    svg_roll_out_jobs = []
    slides_all_layers = {}
    for i in range(len(todo)):
        slide = todo[i]["slide"]
        show_layer_sets = todo[i]["show_layer_sets"]
        slide_dir = os.path.join(work_dir, "slides", slide)

        src_path = os.path.join(slide_dir, "layers.svg")
        src_mtime = utils.mtime(src_path)

        for show_layer_set in show_layer_sets:
            show_label_str = str.join(",", list(show_layer_set))

            dst_path = os.path.join(
                build_dir, "slides", slide, show_label_str + ".svg"
            )

            need_to_roll_out = False
            if not os.path.exists(dst_path):
                reason = "does not exist yet"
                need_to_roll_out = True
            else:
                dst_mtime = utils.mtime(dst_path)
                if src_mtime > dst_mtime:
                    reason = "needs update"
                    need_to_roll_out = True

            if need_to_roll_out:
                if slide not in slides_all_layers:
                    slides_all_layers[
                        slide
                    ] = inkscape.find_inkscape_labels_for_layers_in_inkscape_svg(
                        path=src_path
                    )

                job = {
                    "src_svg_path": src_path,
                    "dst_svg_path": dst_path,
                    "all_layer_set": slides_all_layers[slide],
                    "show_layer_set": show_layer_set,
                }
                svg_roll_out_jobs.append(job)
                if verbose:
                    print(f"roll out: {dst_path:s} because {reason:s}.")

    pool.map(run_svg_roll_out_job, svg_roll_out_jobs)

    # png render
    # ----------
    slide_rendering_need_update = {}
    for slide in resource_updates["slides"]:
        if resource_updates["resources"]:
            slide_rendering_need_update[slide] = True
        else:
            slide_rendering_need_update[slide] = resource_updates["slides"][
                slide
            ]

    render_jobs = []
    list_of_image_paths = []
    for i in range(len(todo)):
        slide = todo[i]["slide"]
        show_layer_sets = todo[i]["show_layer_sets"]

        for show_layer_set in show_layer_sets:
            show_label_str = str.join(",", list(show_layer_set))

            src_path = os.path.join(
                build_dir, "slides", slide, show_label_str + ".svg"
            )
            dst_path = os.path.join(
                build_dir, "slides", slide, show_label_str + ".jpg"
            )

            list_of_image_paths.append(dst_path)

            need_to_render = False

            if slide_rendering_need_update[slide]:
                need_to_render = True

            if not os.path.exists(dst_path):
                reason = "does not exist yet"
                need_to_render = True
            else:
                src_mtime = utils.mtime(src_path)
                dst_mtime = utils.mtime(dst_path)
                if src_mtime > dst_mtime:
                    reason = "needs update"
                    need_to_render = True

            if need_to_render:
                job = {}
                job["src_svg_path"] = src_path
                job["dst_jpg_path"] = dst_path
                job["background_opacity"] = 0.0
                render_jobs.append(job)
                if verbose:
                    print(f"render: {dst_path:s} because {reason:s}.")

    num_render_updates = len(render_jobs)

    pool.map(run_png_render_job, render_jobs)

    # write pdf
    # ---------
    need_to_render_pdf = False
    pdf_path = os.path.join(build_dir, "slides.pdf")

    if not os.path.exists(pdf_path):
        reason = "does not exist yet"
        need_to_render_pdf = True
    else:
        if num_render_updates > 0:
            reason = "needs update"
            need_to_render_pdf = True

    if need_to_render_pdf:
        if verbose:
            print(f"compile pdf because {reason:s}.")
        portable_document_format.images_to_pdf(
            list_of_image_paths=list_of_image_paths, out_path=pdf_path
        )

    if out_path is not None:
        shutil.copy(src=pdf_path, dst=out_path + ".part")
        os.rename(out_path + ".part", out_path)

    return True


def run_svg_roll_out_job(job):
    roll_out_slide_layers(**job)


def roll_out_slide_layers(
    src_svg_path, show_layer_set, all_layer_set, dst_svg_path
):
    show_layer_set = set(show_layer_set)
    all_layer_set = set(all_layer_set)

    hide_layer_set = all_layer_set.difference(show_layer_set)
    show_label_str = str.join(",", list(show_layer_set))
    inkscape.inkscape_svg_export_layers(
        src=src_svg_path,
        dst=dst_svg_path,
        show=show_layer_set,
        hide=hide_layer_set,
    )


def run_png_render_job(job):
    inkscape.inkscape_render(
        svg_path=job["src_svg_path"],
        out_path=job["dst_jpg_path"],
        background_opacity=job["background_opacity"],
    )


def update_latex_slides_and_snippets(
    work_dir, todo=None, pool=None, verbose=True
):
    pool = utils.init_multiprocessing_pool_if_None(pool=pool)

    if todo is None:
        todo = status_of_what_needs_to_be_done(work_dir=work_dir)

    latex_types = {
        "slide": ".png",
        "snippet": ".svg",
    }
    common_resource_dir = os.path.join(work_dir, "resources")

    jobs = []

    for lt in latex_types:
        for src_path in utils.glob(common_resource_dir, f"*.{lt:s}.tex"):
            _src_path, _ = os.path.splitext(src_path)
            dst_path = _src_path + latex_types[lt]
            _job = _make_latex_job(src_path=src_path, dst_path=dst_path)
            if _job is not None:
                _job["latex_type"] = lt
                jobs.append(_job)
                if verbose:
                    print(
                        f"latex render: {dst_path:s} because {_job['reason']:s}."
                    )

        for i in range(len(todo)):
            slide = todo[i]["slide"]
            show_layer_sets = todo[i]["show_layer_sets"]
            slide_dir = os.path.join(work_dir, "slides", slide)

            slide_resource_dir = os.path.join(slide_dir, "resources")

            for src_path in utils.glob(slide_resource_dir, f"*.{lt:s}.tex"):
                _src_path, _ = os.path.splitext(src_path)
                dst_path = _src_path + latex_types[lt]

                _job = _make_latex_job(src_path=src_path, dst_path=dst_path)
                if _job is not None:
                    _job["latex_type"] = lt
                    jobs.append(_job)
                    if verbose:
                        print(
                            f"latex render: {dst_path:s} because {_job['reason']:s}."
                        )

    pool.map(run_latex_render_job, jobs)


def _make_latex_job(src_path, dst_path):
    need_to_render = False

    if not os.path.exists(dst_path):
        reason = "does not exist yet"
        need_to_render = True
    else:
        src_mtime = utils.mtime(src_path)
        dst_mtime = utils.mtime(dst_path)
        if src_mtime > dst_mtime:
            reason = "needs update"
            need_to_render = True

    if need_to_render:
        job = {}
        job["reason"] = reason
        job["src_path"] = src_path
        job["dst_path"] = dst_path
        return job
    else:
        return None


def run_latex_render_job(job):
    if job["latex_type"] == "snippet":
        with open(job["src_path"], "rt") as f:
            latex_string = f.read()

        latex.render_snippet_to_svg(
            latex_string=latex_string,
            out_path=job["dst_path"],
        )

    elif job["latex_type"] == "slide":
        latex.render_slide_to_png(
            latex_path=job["src_path"],
            out_path=job["dst_path"],
        )
    else:
        raise AssertionError(f"No such latex_type {job['latex_type']:s}.")
