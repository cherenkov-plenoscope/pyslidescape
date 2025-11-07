import pygame
import datetime
import PIL.Image
import io


def copy_black_white(surface):
    """
    Returns a black and white copy of the input pygame.Surface.
    """
    out = pygame.Surface(surface.get_size())
    w, h = surface.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surface.get_at((x, y))
            m = int((float(r) + float(g) + float(b)) / 3.0)
            out_color = pygame.Color(m, m, m, a)
            out.set_at((x, y), out_color)
    return out


def write_slides(path, slides, list_of_image_paths):
    """
    Writes a text file for ffmpeg with the paths to the slides and the duration
    of each slide.
    """
    with open(path, "wt") as f:
        for i in range(len(slides)):
            slide = slides[i]
            slide_index, slide_duration = slide

            img_path = list_of_image_paths[slide_index]
            f.write(f"file '{img_path:s}'\n")
            f.write(f"duration {slide_duration:.3f}\n")

        # repeat last image file path to prevent quirks in ffmpeg
        f.write(f"file '{img_path:s}'\n")


def update_display(display, thumbs, slide, thumb_size):
    """
    Display five slides in a row. The current slide is in the center and in
    color. The previous two slides and the trailing two slides are in black
    and white. Slides before the first and after the last slide are filled
    with gray color.
    """
    BACKGROUND_COLOR = (128, 128, 128)

    print(f"Slide {slide:03d}, back: [a], forward: [d]")
    display.fill(BACKGROUND_COLOR)
    tx, ty = thumb_size
    slide_m2 = slide - 2
    slide_m1 = slide - 1
    slide_00 = slide
    slide_p1 = slide + 1
    slide_p2 = slide + 2

    COLOR = 1
    BLACK_AND_WHITE = 2

    if slide_m2 >= 0 and slide_m2 < len(thumbs):
        display.blit(thumbs[slide_m2][BLACK_AND_WHITE], (0, 0 * ty))

    if slide_m1 >= 0 and slide_m1 < len(thumbs):
        display.blit(thumbs[slide_m1][BLACK_AND_WHITE], (0, 1 * ty))

    if slide_00 >= 0 and slide_00 < len(thumbs):
        display.blit(thumbs[slide_00][COLOR], (0, 2 * ty))

    if slide_p1 >= 0 and slide_p1 < len(thumbs):
        display.blit(thumbs[slide_p1][BLACK_AND_WHITE], (0, 3 * ty))

    if slide_p2 >= 0 and slide_p2 < len(thumbs):
        display.blit(thumbs[slide_p2][BLACK_AND_WHITE], (0, 4 * ty))

    pygame.display.flip()


def load_image_as_thumb(path, thumb_size):
    buff = io.BytesIO()
    with PIL.Image.open(path) as img:
        img.thumbnail(thumb_size)
        img.save(buff, format="bmp")
    buff.seek(0)
    gimg = pygame.image.load(buff)
    return gimg


def run_interactive_viewer_for_timing(
    input_path_to_list_of_image_paths,
    output_path_to_ffmpeg_slide_order,
    thumb_size=(192, 108),
):
    # START
    # =====

    # load all slide images
    # ---------------------
    list_of_image_paths = []
    with open(input_path_to_list_of_image_paths, "rt") as fin:
        for line in fin.readlines():
            list_of_image_paths.append(line.strip())

    thumbs = []
    print("loading slide images ", end="")
    for image_path in list_of_image_paths:
        print(".", end="", flush=True)
        gimg = load_image_as_thumb(path=image_path, thumb_size=thumb_size)
        thumbs.append((image_path, gimg, copy_black_white(gimg)))
    print("done.")

    # begin of interactive session
    # ----------------------------

    pygame.init()
    display = pygame.display.set_mode((thumb_size[0], thumb_size[1] * 5))

    slide = 0
    slides = []

    update_display(
        display=display, thumbs=thumbs, slide=slide, thumb_size=thumb_size
    )

    # wait for user to press [s]tart to initiate the timer
    # ----------------------------------------------------

    print("start: [s]")
    waiting = True

    while waiting:
        pygame.time.wait(10)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    time_slide_start = datetime.datetime.now()
                    waiting = False

    update_display(
        display=display, thumbs=thumbs, slide=slide, thumb_size=thumb_size
    )

    # Allow user to move forth and back in slides and measure how long each slide
    # is shown.
    # ---------------------------------------------------------------------------

    while True:
        pygame.time.wait(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                write_slides(
                    path=output_path_to_ffmpeg_slide_order,
                    slides=slides,
                    list_of_image_paths=list_of_image_paths,
                )
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a and slide - 1 >= 0:
                    time_slide_stop = datetime.datetime.now()
                    duration_slide = (
                        time_slide_stop - time_slide_start
                    ).total_seconds()
                    time_slide_start = time_slide_stop

                    slides.append((slide, duration_slide))
                    slide -= 1
                    update_display(
                        display=display,
                        thumbs=thumbs,
                        slide=slide,
                        thumb_size=thumb_size,
                    )
                    break

                elif event.key == pygame.K_d and slide + 1 < len(thumbs):
                    time_slide_stop = datetime.datetime.now()
                    duration_slide = (
                        time_slide_stop - time_slide_start
                    ).total_seconds()
                    time_slide_start = time_slide_stop

                    slides.append((slide, duration_slide))
                    slide += 1
                    update_display(
                        display=display,
                        thumbs=thumbs,
                        slide=slide,
                        thumb_size=thumb_size,
                    )
                    break
