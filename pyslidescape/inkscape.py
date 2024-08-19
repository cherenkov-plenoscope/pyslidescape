from xml.dom import minidom
import tempfile
import os
import subprocess


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
                if "layer" in g.attributes["id"].value:
                    inkscape_labels.append(
                        g.attributes["inkscape:label"].value
                    )
    return inkscape_labels


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


def init_slide_svg(num_pixel_width, num_pixel_height, docname="slide"):
    assert num_pixel_width > 0
    assert num_pixel_height > 0

    svg = """
    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <!-- Created with Inkscape (http://www.inkscape.org/) -->

    <svg
        width="{num_pixel_width:d}px"
        height="{num_pixel_height:d}px"
        viewBox="0 0 {num_pixel_width:d} {num_pixel_height:d}"
        version="1.1"
        id="SVGRoot"
        inkscape:version="1.2.2 (b0a8486541, 2022-12-01)"
        sodipodi:docname="{docname:s}"
        xml:space="preserve"
        xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
        xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
        xmlns="http://www.w3.org/2000/svg"
        xmlns:svg="http://www.w3.org/2000/svg">
    </svg>
    """
    return svg
