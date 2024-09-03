from .version import __version__
from . import inkscape
from . import utils
from . import portable_document_format
from . import template
from . import latex
from . import layers_txt
from . import notes_img

import os
import shutil
import warnings
import multiprocessing


def add_slide(work_dir, slide_name, slide_format=None):
    slide_dir = os.path.join(work_dir, "slides", slide_name)
    assert not os.path.exists(
        slide_dir
    ), f"The slide '{slide_name:s}' already exists."

    if slide_format is None:
        slidescape_dir = os.path.join(work_dir, ".slidescape")
        template_slide_dir = os.path.join(slidescape_dir, "template_slide")

        if os.path.isdir(template_slide_dir):
            shutil.copytree(src=template_slide_dir, dst=slide_dir)
        else:
            presentation_config = utils.read_json_to_dict(
                os.path.join(slidescape_dir, "config.json")
            )
            slide_format = presentation_config["slide_format"]
            template.init_slide_dir(path=slide_dir, slide_format=slide_format)
    else:
        template.init_slide_dir(path=slide_dir, slide_format=slide_format)


def compile(work_dir, out_path=None, pool=None, verbose=True, notes=False):
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
    todo = utils.init_todo(work_dir=work_dir)

    build_dir = os.path.join(work_dir, ".build")
    os.makedirs(build_dir, exist_ok=True)

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

    # make slide dirs
    # ---------------
    for i in range(len(todo)):
        slide = todo[i]["slide"]
        slide_dir = os.path.join(build_dir, "slides", slide)
        os.makedirs(slide_dir, exist_ok=True)

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
                reason = "resources updated"

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

    # notes
    # -----
    if notes:
        _render_notes(work_dir=work_dir, todo=todo, pool=pool, verbose=verbose)

        need_to_render_notes_pdf = False
        notes_pdf_path = os.path.join(build_dir, "slides.notes.pdf")
        list_of_slides_with_notes_paths = []
        for p_slide in list_of_image_paths:
            p_slide_woext, _ = os.path.splitext(p_slide)
            p_slide_with_notes = p_slide_woext + ".sn.jpg"
            list_of_slides_with_notes_paths.append(p_slide_with_notes)
        portable_document_format.images_to_pdf(
            list_of_image_paths=list_of_slides_with_notes_paths,
            out_path=notes_pdf_path,
        )

    if out_path is not None:
        shutil.copy(src=pdf_path, dst=out_path + ".part")
        os.rename(out_path + ".part", out_path)

        if notes:
            notes_pdf_path = os.path.join(build_dir, "slides.notes.pdf")
            out_path_wo_ext, ext = os.path.splitext(out_path)
            notes_out_path = out_path_wo_ext + ".notes" + ext
            shutil.copy(src=notes_pdf_path, dst=notes_out_path + ".part")
            os.rename(notes_out_path + ".part", notes_out_path)

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


def _render_notes(work_dir, todo=None, pool=None, verbose=True):
    pool = utils.init_multiprocessing_pool_if_None(pool=pool)
    todo = utils.init_todo_if_None(todo=todo, work_dir=work_dir)

    build_dir = os.path.join(work_dir, ".build")

    jobs = []
    for i in range(len(todo)):
        slide = todo[i]
        slide_key = slide["slide"]
        slide_dir = os.path.join(build_dir, "slides", slide_key)
        for layers_key in slide["notes"]:
            mem_basename = layers_key + ".notes"
            mem_path = os.path.join(slide_dir, mem_basename)
            cur_notes = slide["notes"][layers_key]

            need_to_render_note = False

            if os.path.exists(mem_path):
                mem_notes = utils.read_lines_from_textfile(mem_path)
                if mem_notes != cur_notes:
                    if verbose:
                        print(f"update notes {slide_key:s}/{layers_key:s}")
                    utils.write_lines_to_textfile(
                        path=mem_path, lines=cur_notes
                    )
                    need_to_render_note = True
            else:
                if verbose:
                    print(f"init notes {slide_key:s}/{layers_key:s}")
                utils.write_lines_to_textfile(path=mem_path, lines=cur_notes)
                need_to_render_note = True

            slide_with_notes_path = os.path.join(
                slide_dir, layers_key + ".sn.jpg"
            )
            if not os.path.exists(slide_with_notes_path):
                if verbose:
                    print(f"render notes {slide_key:s}/{layers_key:s}")
                need_to_render_note = True
            else:
                slide_path = os.path.join(slide_dir, layers_key + ".jpg")
                slide_mtime = utils.mtime(slide_path)
                slide_with_notes_mtime = utils.mtime(slide_with_notes_path)
                if slide_mtime > slide_with_notes_mtime:
                    if verbose:
                        print(
                            "update notes because slide got updated "
                            f"{slide_key:s}/{layers_key:s}"
                        )
                    need_to_render_note = True

            if need_to_render_note:
                jobs.append(
                    {
                        "work_dir": work_dir,
                        "slide_key": slide_key,
                        "layers_key": layers_key,
                    }
                )

    pool.map(_run_job_render_note, jobs)


def update_latex_slides_and_snippets(
    work_dir, todo=None, pool=None, verbose=True
):
    pool = utils.init_multiprocessing_pool_if_None(pool=pool)
    todo = utils.init_todo_if_None(todo=todo, work_dir=work_dir)

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
                        f"latex render: {dst_path:s} "
                        f"because {_job['reason']:s}."
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
                            f"latex render: {dst_path:s} "
                            f"because {_job['reason']:s}."
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
        job["fontcolor"] = "white"
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
            fontcolor=job["fontcolor"],
        )

    elif job["latex_type"] == "slide":
        latex.render_slide_to_png(
            latex_path=job["src_path"],
            out_path=job["dst_path"],
        )
    else:
        raise AssertionError(f"No such latex_type {job['latex_type']:s}.")


def _run_job_render_note(job):
    build_dir = os.path.join(job["work_dir"], ".build")
    slide_dir = os.path.join(build_dir, "slides", job["slide_key"])
    notes_path = os.path.join(slide_dir, job["layers_key"] + ".notes")
    notes_render_path = notes_path + ".jpg"
    notes_lines = utils.read_lines_from_textfile(notes_path)
    notes_text = "\n".join(notes_lines)
    notes_img.render_text_to_image(
        path=notes_render_path,
        text=notes_text,
    )

    slide_render_path = os.path.join(slide_dir, job["layers_key"] + ".jpg")
    slide_with_notes_path = os.path.join(
        slide_dir, job["layers_key"] + ".sn.jpg"
    )

    notes_img.stack_images(
        out_path=slide_with_notes_path,
        input_paths=[slide_render_path, notes_render_path],
    )
