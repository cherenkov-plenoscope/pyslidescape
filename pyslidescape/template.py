from . import utils
from . import inkscape

import os
import shutil
import textwrap


def default_presentation_config():
    return {"slide_format": deafault_slide_format()}


def deafault_slide_format():
    return {
        "num_pixel_width": 1920,
        "num_pixel_height": 1080,
    }


def init_example_presentation(work_dir, presentation_config=None):
    """
    A minimal example presentation with some basic features.
    """
    if presentation_config is None:
        presentation_config = default_presentation_config()

    os.makedirs(work_dir, exist_ok=True)
    utils.write_dict_to_json(
        os.path.join(work_dir, ".config.json"), presentation_config
    )

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
            text="It is linked via: '../../resources/logo.jpg'.",
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
        make_text_element(x=800, y=750, text="My work.", font_size=48),
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
        slide_format=presentation_config["slide_format"],
    )

    base = element_join(
        make_text_element(x=100, y=100, text="This is my work", font_size=64),
        make_image_element(
            x=200, y=300, dx=320, dy=320, href="../../resources/logo.jpg"
        ),
    )

    wait = element_join(
        make_text_element(x=800, y=750, text="wait for it...", font_size=48),
    )

    work = element_join(
        make_image_element(
            x=1000,
            y=200,
            dx=480,
            dy=480,
            href="resources/explode.jpg",
        ),
        make_text_element(x=800, y=750, text="boom.", font_size=48),
    )

    content = element_join(
        make_inkscape_layer(content=base, label="base"),
        make_inkscape_layer(content=wait, label="wait"),
        make_inkscape_layer(content=work, label="work"),
    )

    init_slide_dir(
        path=os.path.join(slides_dir, "my_work"),
        content=content,
        resources=["explode.jpg"],
        show_layer_set=["base", "base,wait", "base,work"],
        slide_format=presentation_config["slide_format"],
    )

    base = element_join(
        make_text_element(
            x=100, y=100, text="Happy Appendix everyone!", font_size=64
        ),
        make_image_element(
            x=200, y=300, dx=320, dy=320, href="../../resources/logo.jpg"
        ),
    )
    also = element_join(
        make_text_element(
            x=600, y=500, text="Also: Latex snippets.", font_size=64
        ),
        make_image_element(
            x=950, y=600, href="resources/example_LaTex.snippet.svg"
        ),
    )
    math = element_join(
        make_image_element(
            x=0,
            y=0,
            dx=1920,
            dy=1080,
            href="resources/example_LaTex.slide.png",
        ),
    )
    content = element_join(
        make_inkscape_layer(content=math, label="math"),
        make_inkscape_layer(content=also, label="also"),
        make_inkscape_layer(content=base, label="base"),
    )

    init_slide_dir(
        path=os.path.join(slides_dir, "appendix"),
        content=content,
        resources=["example_LaTex.slide.tex", "example_LaTex.snippet.tex"],
        show_layer_set=["base", "also,base", "math,base"],
        slide_format=presentation_config["slide_format"],
    )

    slides_txt_path = os.path.join(work_dir, "slides.txt")
    with open(slides_txt_path, "wt") as f:
        f.write("welcome\n")
        f.write("my_work\n")
        f.write("appendix\n")


def init_slide_dir(
    path, content="", resources=[], show_layer_set=[], slide_format=None
):
    if slide_format is None:
        slide_format = deafault_slide_format()

    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "resources"), exist_ok=True)
    for resource in resources:
        shutil.copy(
            src=os.path.join(utils.get_resources_dir(), resource),
            dst=os.path.join(path, "resources", resource),
        )

    slide_path = os.path.join(path, "layers.svg")
    with open(slide_path, "wt") as f:
        f.write(make_slide(slide_format=slide_format, content=content))

    layer_order_path = os.path.join(path, "layers.txt")
    with open(layer_order_path, "wt") as f:
        for l in show_layer_set:
            f.write(l + "\n")


def make_slide(slide_format, content=""):
    sf = slide_format
    assert sf["num_pixel_width"] > 0
    assert sf["num_pixel_height"] > 0
    w = sf["num_pixel_width"]
    h = sf["num_pixel_height"]

    svg = ""
    svg += '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg += "<!-- Created with pyslidescape (https://github.com/cherenkov-plenoscope/pyslidescape/) -->\n"
    svg += "\n"
    svg += "<svg\n"
    svg += f'    width="{w:.1f}px"\n'
    svg += f'    height="{h:.1f}px"\n'
    svg += f'    viewBox="0 0 {w:.1f} {h:.1f}"\n'
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


def make_image_element(x, y, href, dx=None, dy=None, uid=123):
    svg = ""
    svg += "<image\n"
    if dx is not None:
        svg += f'    width="{dx:f}"\n'
    if dy is not None:
        svg += f'    height="{dy:f}"\n'
    svg += '    preserveAspectRatio="none"\n'
    svg += f'    xlink:href="{href:s}"\n'
    svg += f'    id="image{uid:d}"\n'
    svg += f'    x="{x:f}"\n'
    svg += f'    y="{y:f}"\n'
    svg += '    style="display:inline"\n'
    svg += "/>"
    return svg
