import argparse
import signal
import sys
from importlib import import_module

from openbakery import __version__
from openbakery.commands.check_profile import main as check_profile_main

SUBCOMMANDS = [
    "adobefonts",
    "fontbureau",
    "fontval",
    "fontwerk",
    "googlefonts",
    "iso15008",
    "notofonts",
    "opentype",
    "shaping",
    "ufo-sources",
    "universal",
    "proposals",
    "check-profile",
]


def run_profile_check(profilename):
    module = import_module(f"openbakery.profiles.{profilename.replace('-', '_')}")
    sys.exit(check_profile_main(module.profile))


def signal_handler(sig, frame):
    print("\nCancelled by user")
    sys.exit(-1)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) >= 2 and sys.argv[1] in SUBCOMMANDS:
        subcommand = sys.argv[1]

        sys.argv[0] += " " + subcommand
        del sys.argv[1]  # Make this indirection less visible for subcommands.

        if subcommand == "check-profile":
            check_profile_main()
        else:
            run_profile_check(subcommand)

    else:
        description = (
            "Run openbakery subcommands. Subcommands have their own help messages;\n"
            "to view them add the '-h' (or '--help') option after the subcommand,\n"
            "like in this example:\n    openbakery universal -h"
        )

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter, description=description
        )
        parser.add_argument(
            "subcommand",
            help="The subcommand to execute",
            nargs="?",
            choices=SUBCOMMANDS,
        )
        parser.add_argument(
            "--list-subcommands",
            action="store_true",
            help="print list of supported subcommands",
        )
        parser.add_argument("--version", action="version", version=__version__)
        args = parser.parse_args()

        if args.list_subcommands:
            print("\n".join(SUBCOMMANDS))
        else:
            parser.print_help()
