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
    commands = parser.add_subparsers(help="Commands", dest="command")


    # init
    # ----
    init_cmd = commands.add_parser(
        "init", help="Initialize a presentation template."
    )
    init_cmd.add_argument(
        "path",
        metavar="PATH",
        type=str,
        help=("Path to init the template presentation in."),
    )

    # compile
    # =======
    compile_cmd = commands.add_parser(
        "compile", help="Compiles the slices into a production ready PDF."
    )
    compile_cmd.add_argument(
        "work_dir",
        metavar="IN_PATH",
        type=str,
        help=("The working directory to contain the raw presentation slides."),
    )
    compile_cmd.add_argument(
        "out_path",
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

    # slide
    # =====
    slide_cmd = commands.add_parser(
        "slide", help="Writes an empty slide in svg to a path."
    )
    slide_cmd.add_argument(
        "out_path",
        metavar="PATH",
        type=str,
        help=("Path of the empty slide."),
    )

    # render latex slide
    # ------------------
    latex_cmd = commands.add_parser(
        "latex", help="Renders a latex slide.tex into a png image."
    )
    latex_cmd.add_argument(
        "latex_path",
        metavar="IN_PATH",
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

    if args.command == "init":
        pyslidescape.template.init(work_dir=args.path)
    elif args.command == "compile":
        pyslidescape.make(
            work_dir=args.work_dir,
            out_path=args.out_path,
            pool=multiprocessing.Pool(args.num_threads),
        )
    elif args.command == "slide":
        pyslidescape.write_template_slide(
            out_path=args.out_path,
        )
    elif args.command == "latex":
        pyslidescape.latex.render_slide_into_png(
            latex_path=args.latex_path, out_path=args.out_path
        )
    else:
        print("No or unknown command.")
        parser.print_help()
        sys.exit(17)


if __name__ == "__main__":
    main()
