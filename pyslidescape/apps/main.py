import pyslidescape
import argparse
import os
import sys
import multiprocessing


def main():
    parser = argparse.ArgumentParser(
        prog="pyslidescape",
        description="Make presentation slides from images and vector drawings.",
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Print the version."
    )

    commands = parser.add_subparsers(help="Commands", dest="command")

    # init
    # ----
    init_cmd = commands.add_parser(
        "init", help="Initialize a presentation template."
    )
    add_work_dir_argument_to_command(cmd=init_cmd)

    # compile
    # =======
    compile_cmd = commands.add_parser(
        "compile", help="Compiles the slices into a production ready PDF."
    )
    add_work_dir_argument_to_command(cmd=compile_cmd)
    compile_cmd.add_argument(
        "out_path",
        nargs="?",
        default=None,
        metavar="OUT_PATH",
        type=str,
        help=("Path of the output PDF."),
    )
    compile_cmd.add_argument(
        "-i",
        "--num_threads",
        metavar="NUM_THREADS",
        type=int,
        help=("The number of threads to use."),
        required=False,
        default=1,
    )
    compile_cmd.add_argument(
        "--verbose", action="store_true", help="Print what is done."
    )

    # slide
    # =====
    slide_cmd = commands.add_parser(
        "add-slide", help="Adds a new and empty slide to the presentation."
    )
    add_work_dir_argument_to_command(cmd=slide_cmd)
    slide_cmd.add_argument(
        "slide_name",
        metavar="SLIDE_NAME",
        type=str,
        help=("The name of the new slide."),
    )

    # render latex slide
    # ------------------
    latex_cmd = commands.add_parser(
        "latex", help="Renders a latex slide.tex into a png image."
    )
    latex_cmd.add_argument(
        "latex_path",
        metavar="LATEX_PATH",
        type=str,
        help=("Path to the input latex slide.tex"),
    )
    latex_cmd.add_argument(
        "out_path",
        metavar="OUT_PATH",
        type=str,
        help=("Path to the output png image"),
    )

    args = parser.parse_args()

    if args.version:
        print(pyslidescape.__version__)
        return 0

    if args.command == "init":
        pyslidescape.template.init_example_presentation(work_dir=args.work_dir)
    elif args.command == "compile":
        pyslidescape.compile(
            work_dir=args.work_dir,
            out_path=args.out_path,
            pool=pyslidescape.utils.init_multiprocessing_pool(
                args.num_threads
            ),
            verbose=args.verbose,
        )
    elif args.command == "add-slide":
        pyslidescape.add_slide(
            work_dir=args.work_dir,
            slide_name=args.slide_name,
        )
    elif args.command == "latex":
        pyslidescape.latex.render_slide_to_png(
            latex_path=args.latex_path, out_path=args.out_path
        )
    else:
        print("No or unknown command.")
        parser.print_help()
        sys.exit(17)


def add_work_dir_argument_to_command(cmd):
    cmd.add_argument(
        "work_dir",
        nargs="?",
        default=os.curdir,
        metavar="WORK_DIR",
        type=str,
        help=("The working directory to contain the raw presentation slides."),
    )


if __name__ == "__main__":
    main()
