import os
import subprocess


def render_slide_into_png(
    latex_path, out_path=None, num_pixel_width=1920, num_pixel_height=1080
):
    assert num_pixel_width > 0
    assert num_pixel_height > 0
    src_path, tex_ext = os.path.splitext(latex_path)
    cwd = os.path.dirname(src_path)
    assert tex_ext == ".tex"
    pdf_path = src_path + ".pdf"
    aux_path = src_path + ".aux"
    log_path = src_path + ".log"
    png_path = src_path + ".png"
    std_path = src_path + ".std"
    assert not os.path.exists(
        pdf_path
    ), f"Did not expect the pdf '{pdf_path:s}' to exist. I stop here to not overwrite the existing pdf."

    pdflatex_call = ["pdflatex", latex_path]
    with open(std_path, "wt") as f:
        rc = subprocess.call(
            pdflatex_call, cwd=cwd, stdout=f, stderr=subprocess.STDOUT
        )
    if rc == 0:
        os.remove(aux_path)
        os.remove(log_path)
        os.remove(std_path)
    else:
        s_pdflatex_call = str.join(" ", pdflatex_call)
        raise Exception(
            f"Failed to call '{s_pdflatex_call:s}'. See {std_path:s} for more details."
        )

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
    rc = subprocess.call(pdftoppm_call, cwd=cwd)

    if rc == 0:
        out_file_written_by_pdftoppm = png_path + "-1.png"
        os.rename(out_file_written_by_pdftoppm, png_path)
        os.remove(pdf_path)
    else:
        s_pdftoppm_call = str.join(" ", pdftoppm_call)
        raise Exception(f"Failed to call '{s_pdftoppm_call:s}'.")

    if out_path is not None:
        os.rename(png_path, out_path)
