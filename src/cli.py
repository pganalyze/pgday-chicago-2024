"""Command-line interface."""


import argparse


def get_cli_args():
    """Return a dictionary of the CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Using constraint programming for automatic index selection")

    parser.add_argument(
        "-d",
        "--data",
        required=True,
        metavar="FILE",
        nargs=1,
        type=str,
        help="JSON data file")

    parser.add_argument(
        "-s",
        "--settings",
        metavar="FILE",
        nargs=1,
        default=None,
        type=str,
        help="JSON settings file")

    parser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="display solving process")

    args = parser.parse_args()

    return {"Data JSON": args.data[0],
            "Settings JSON": None if args.settings is None else args.settings[0],
            "Verbose": args.verbose}
