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


def join_indent(elements):
    if len(elements) > 0:
        return "    " + str.join("\n    ", elements) + "\n"
    else:
        return ""


def init_slide_svg(num_pixel_width, num_pixel_height, elements=[]):
    assert num_pixel_width > 0
    assert num_pixel_height > 0

    svg = ""
    svg += '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg += "<!-- Created with pyslidescape (https://github.com/cherenkov-plenoscope/pyslidescape/) -->\n"
    svg += "\n"
    svg += "<svg\n"
    svg += f'    width="{num_pixel_width:d}px"\n'
    svg += f'    height="{num_pixel_height:d}px"\n'
    svg += f'    viewBox="0 0 {num_pixel_width:d} {num_pixel_height:d}"\n'
    svg += '    version="1.1"\n'
    svg += '    id="SVGRoot"\n'
    svg += '    xmlns="http:www.w3.org/2000/svg"\n'
    svg += '    xmlns:svg="http://www.w3.org/2000/svg">\n'
    svg += join_indent(elements)
    svg += "</svg>\n"
    return svg


def make_text_element(text, x, y, font_size, font_family="Waree", uid=123):
    return f"""
    <text
         xml:space="preserve"
         style="font-size:{font_size:f}px;font-family:{font_family:s};text-align:center;text-anchor:middle;display:inline;fill:#000000;fill-opacity:0;stroke-width:5"
         x="{x:f}"
         y="{y:f}"
         id="text{uid:d}">
        {text:s}
    </text>
    """


def make_rect_element(x, y, dx, dy, uid=123):
    return f"""
    <rect
         style="fill:#000000;stroke-width:5"
         id="rect{uid:d}"
         width="{dx:f}"
         height="{dy:f}"
         x="{x:f}"
         y="{y:f}"
    />
    """


def make_inkscape_layer(label, elements, uid=123):
    svg = ""
    svg += "<g\n"
    svg += '    inkscape:groupmode="layer"\n'
    svg += f'    id="layer{uid:d}"\n'
    svg += f'    inkscape:label="{label:s}"\n'
    svg += '    style="display:inline">\n'
    svg += join_indent(elements)
    svg += "</g>\n"
    return svg


def make_image_element(x, y, dx, dy, href, uid=123):
    return f"""
    <image
         width="{dx:f}"
         height="{dy:f}"
         preserveAspectRatio="none"
         xlink:href="{href:s}"
         id="image{uid:d}"
         x="{x:f}"
         y="{y:f}"
         style="display:inline"
    />
    """
