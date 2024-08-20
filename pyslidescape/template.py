from . import utils
from . import inkscape

import os
import shutil
import textwrap


def init(work_dir):
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.join(work_dir, "resources"), exist_ok=True)
    _fname = "logo.jpg"
    shutil.copy(
        os.path.join(utils.get_resources_dir(), _fname),
        os.path.join(work_dir, "resources", _fname),
    )

    slides_dir = os.path.join(work_dir, "slides")
    os.makedirs(slides_dir, exist_ok=True)

    one = element_join(
        make_text_element(
            x=100, y=100, text="Welcom to my presentation!", font_size=64
        ),
        make_image_element(
            x=200, y=300, dx=320, dy=320, href="../../resources/logo.jpg"
        ),
        make_text_element(x=0, y=700, text="This is my logo.", font_size=48),
        make_text_element(
            x=0, y=760, text="It is no many slides.", font_size=48
        ),
        make_text_element(
            x=0,
            y=820,
            text="It linked via: '../../resources/logo.jpg'.",
            font_size=48,
        ),
    )

    two = element_join(
        make_image_element(
            x=1000,
            y=200,
            dx=480,
            dy=480,
            href="resources/work_in_progress_placeholder.svg",
        ),
        make_text_element(x=800, y=700, text="My work.", font_size=48),
    )

    content = element_join(
        make_inkscape_layer(content=one, label="one"),
        make_inkscape_layer(content=two, label="two"),
    )

    init_slide_dir(
        path=os.path.join(slides_dir, "welcome"),
        content=content,
        resources=["work_in_progress_placeholder.svg"],
        show_layer_set=["one", "one,two"],
    )

    init_slide_dir(
        path=os.path.join(slides_dir, "my_work"),
        content="",
        resources=[],
        show_layer_set=["first", "first,second"],
    )

    slides_txt_path = os.path.join(work_dir, "slides.txt")
    with open(slides_txt_path, "wt") as f:
        f.write("welcome\n")
        f.write("my_work\n")


def init_slide_dir(path, content="", resources=[], show_layer_set=[]):
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "resources"), exist_ok=True)
    for resource in resources:
        shutil.copy(
            src=os.path.join(utils.get_resources_dir(), resource),
            dst=os.path.join(path, "resources", resource),
        )

    slide_path = os.path.join(path, "layers.svg")
    with open(slide_path, "wt") as f:
        f.write(make_slide(1920, 1080, content=content))

    layer_order_path = os.path.join(path, "layers.txt")
    with open(layer_order_path, "wt") as f:
        for l in show_layer_set:
            f.write(l + "\n")


def make_slide(num_pixel_width=1920, num_pixel_height=1080, content=""):
    assert num_pixel_width > 0
    assert num_pixel_height > 0

    svg = ""
    svg += '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg += "<!-- Created with pyslidescape (https://github.com/cherenkov-plenoscope/pyslidescape/) -->\n"
    svg += "\n"
    svg += "<svg\n"
    svg += f'    width="{num_pixel_width:.1f}px"\n'
    svg += f'    height="{num_pixel_height:.1f}px"\n'
    svg += f'    viewBox="0 0 {num_pixel_width:.1f} {num_pixel_height:.1f}"\n'
    svg += '    version="1.1"\n'
    svg += '    id="SVGRoot"\n'
    svg += '    xmlns="http://www.w3.org/2000/svg"\n'
    svg += '    xmlns:svg="http://www.w3.org/2000/svg"\n'
    svg += '    xmlns:xlink="http://www.w3.org/1999/xlink"\n'
    svg += (
        '    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" >\n'
    )
    svg += textwrap.indent(content, prefix="    ")
    svg += "</svg>\n"
    return svg


def element_join(*args):
    if len(args) > 0:
        return str.join("\n", args) + "\n"
    else:
        return ""


def make_text_element(text, x, y, font_size, font_family="Waree", uid=123):
    return f"""
    <text
        xml:space="preserve"
        style="font-size:{font_size:f}px;font-family:{font_family:s};stroke-width:5"
        x="{x:f}"
        y="{y:f}"
        id="text{uid:d}" >
        {text:s}
    </text>"""


def make_rect_element(x, y, dx, dy, uid=123):
    return f"""
    <rect
        style="fill:#000000;stroke-width:5"
        id="rect{uid:d}"
        width="{dx:f}"
        height="{dy:f}"
        x="{x:f}"
        y="{y:f}"
    />"""


def make_inkscape_layer(label, content, uid=123):
    svg = ""
    svg += "<g\n"
    svg += '    inkscape:groupmode="layer"\n'
    svg += f'    id="layer{uid:d}"\n'
    svg += f'    inkscape:label="{label:s}"\n'
    svg += '    style="display:inline" >\n'
    svg += textwrap.indent(content, prefix="    ")
    svg += "</g>"
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
    />"""
