import argparse
import logging
import os
import sys

from cppimport import build_all, build_filepath


def _run_from_commandline(raw_args):
    parser = argparse.ArgumentParser("cppimport")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Increase log verbosity."
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Only print critical log messages."
    )

    subparsers = parser.add_subparsers(dest="action")

    build_parser = subparsers.add_parser(
        "build",
        help="Build one or more cpp source files.",
    )
    build_parser.add_argument(
        "root",
        help="The file or directory to build. If a directory is given, "
        "cppimport walks it recursively to build all eligible source "
        "files.",
        nargs="*",
    )

    args = parser.parse_args(raw_args[1:])

    if args.quiet:
        logging.basicConfig(level=logging.CRITICAL)
    elif args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.action == "build":
        for path in args.root or ["."]:
            path = os.path.abspath(os.path.expandvars(path))
            if os.path.isfile(path):
                build_filepath(path)
            elif os.path.isdir(path):
                build_all(path or os.getcwd())
            else:
                raise FileNotFoundError(
                    f'The given root path "{path}" could not be found.'
                )


if __name__ == "__main__":
    _run_from_commandline(sys.argv)
