import os
import subprocess
import tempfile
import shutil
import svgutils


def render_slide_to_png(
    latex_path, out_path=None, num_pixel_width=1920, num_pixel_height=1080
):
    assert num_pixel_width > 0
    assert num_pixel_height > 0
    src_path, tex_ext = os.path.splitext(latex_path)
    cwd = os.path.dirname(src_path)
    latex_basename = os.path.basename(latex_path)
    assert tex_ext == ".tex"
    pdf_path = src_path + ".pdf"
    aux_path = src_path + ".aux"
    log_path = src_path + ".log"
    png_path = src_path + ".png"
    assert not os.path.exists(
        pdf_path
    ), f"Did not expect the pdf '{pdf_path:s}' to exist. I stop here to not overwrite the existing pdf."

    assert os.path.isfile(latex_path)
    safe_sub_call(["pdflatex", latex_basename], cwd=cwd)
    os.remove(aux_path)
    os.remove(log_path)

    pdftoppm_call = [
        "pdftoppm",
        "-scale-to-x",
        f"{num_pixel_width:d}",
        "-scale-to-y",
        f"{num_pixel_height:d}",
        "-f",
        "1",
        "-png",
        pdf_path,
        png_path,
    ]
    safe_sub_call(pdftoppm_call)
    out_file_written_by_pdftoppm = png_path + "-1.png"
    os.rename(out_file_written_by_pdftoppm, png_path)
    os.remove(pdf_path)

    if out_path is not None:
        os.rename(png_path, out_path)


def render_snippet_to_svg(
    latex_string,
    out_path,
    scale=8.0,
    width_of_the_document_in_inches=6.5,
    TMP_DIR=None,
    fontcolor=None,
):
    doc = ""
    doc += "\\documentclass{{article}}\n"
    doc += "\\pagestyle{empty}\n"
    doc += "\\usepackage{amsmath,amssymb,amsfonts,amsthm}\n"
    doc += "\\usepackage{booktabs}\n"
    doc += "\\usepackage{xcolor}\n"
    doc += usepackage_geometry(total=[width_of_the_document_in_inches, 8.75])
    doc += "\n"
    if fontcolor is not None:
        doc += "\\color{" + fontcolor + "}\n"
    doc += "\\begin{document}\n"
    doc += "\n{:s}\n\n".format(latex_string)
    doc += "\\end{document}\n"

    with tempfile.TemporaryDirectory(prefix="pyslidescape-latex-") as tmp_dir:
        if TMP_DIR is not None:
            tmp_dir = TMP_DIR
            os.makedirs(tmp_dir, exist_ok=True)
        with open(os.path.join(tmp_dir, "snip.tex"), "wt") as f:
            f.write(doc)

        safe_sub_call(["pdflatex", "snip.tex"], cwd=tmp_dir)
        safe_sub_call(["pdfcrop", "snip.pdf", "snip_crop.pdf"], cwd=tmp_dir)
        safe_sub_call(
            ["pdf2svg", "snip_crop.pdf", "snip_crop.svg"], cwd=tmp_dir
        )

        _svg = svgutils.transform.fromfile(
            os.path.join(tmp_dir, "snip_crop.svg")
        )
        originalSVG = svgutils.compose.SVG(
            os.path.join(tmp_dir, "snip_crop.svg")
        )
        originalSVG.scale(scale)
        h_val, h_unit = split_unit_str(_svg.height)
        w_val, w_unit = split_unit_str(_svg.width)
        figure = svgutils.compose.Figure(
            "{:f}{:s}".format(w_val * scale, w_unit),
            "{:f}{:s}".format(h_val * scale, h_unit),
            originalSVG,
        )
        figure.save(os.path.join(tmp_dir, "snip_crop_scale.svg"))
        shutil.move(os.path.join(tmp_dir, "snip_crop_scale.svg"), out_path)


def safe_sub_call(command, cwd=None):
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_std_path = os.path.join(tmp_dir, "std")
        with open(tmp_std_path, "wb") as f:
            rc = subprocess.call(
                command,
                cwd=cwd,
                stdout=f,
                stderr=subprocess.STDOUT,
            )
        if rc != 0:
            with open(tmp_std_path, "rb") as f:
                print(f.read())
            cmd_str = str.join(" ", command)
            raise Exception(f"Failed to call '{cmd_str:s}'.")


def split_unit_str(text):
    for i, c in enumerate(text):
        if not c.isdigit():
            break
    number = float(text[:i])
    unit = text[i:]
    return number, unit


def usepackage_geometry(
    total=[6.5, 8.75], top=1.2, left=0.9, includefoot=True
):
    o = "\\usepackage["
    o += "total={{{:.1f}in,{:.1f}in}}, ".format(total[0], total[1])
    o += "top={:.1f}in, ".format(top)
    o += "left={:.1f}in, ".format(left)
    if includefoot:
        o += "includefoot"
    o += "]{geometry}"
    return o
