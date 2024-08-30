import PIL as pil
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import textwrap


lorem_ipsum = """
Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy
eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet
clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit
amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat,
sed diam voluptua. At vero eos et accusam et justo duo dolores et ea
rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum
dolor sit amet.
"""

def render_text_to_image(
    path,
    text,
    num_cols = 1920,
    num_rows = 1080,
    background_color = (128, 128, 128),
    font_color = (0, 0, 0),
    num_character_columns = 80,
):
    _text = textwrap.wrap(
        text=text,
        width=num_character_columns,
    )
    _text = "\n".join(_text)

    img = pil.Image.new('RGB', (num_cols, num_rows), background_color)
    font = pil.ImageFont.truetype('DejaVuSansMono.ttf', size=36)

    draw = pil.ImageDraw.Draw(img)
    # left aligned horizontally, top aligned  vertically
    # a means ascender of the first line, which is the top of the string

    draw.multiline_text(
        xy=(50, 50),
        text=status_text,
        font=font,
        anchor='la',
        fill=font_color,
    )
    img.save(path)
