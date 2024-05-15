import pyslidescape
import argparse
import os
import shutil
from importlib import resources as importlib_resources
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="pyslidescape",
        description="Make presentation slides from images and vector drawings.",
    )
    commands = parser.add_subparsers(help="Commands", dest="command")

    # compile
    # =======
    compile_cmd = commands.add_parser(
        "compile", help="Compiles the slices into a production ready PDF."
    )
    compile_cmd.add_argument(
        "work_dir",
        metavar="PATH",
        type=str,
        help=("The working directory to contain the raw presentation slides."),
    )
    compile_cmd.add_argument(
        "out_path",
        metavar="PATH",
        type=str,
        help=("Path of the output PDF."),
    )
    compile_cmd.add_argument(
        "-i",
        "--num_threads",
        metavar="NUM",
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

    args = parser.parse_args()

    if args.command == "compile":
        pyslidescape.compile(
            work_dir=args.work_dir,
            out_path=args.out_path,
            num_threads=args.num_threads,
        )
    elif args.command == "slide":
        pyslidescape.write_template_slide(
            out_path=args.out_path,
        )

    else:
        print("No or unknown command.")
        parser.print_help()
        sys.exit(17)


if __name__ == "__main__":
    main()
