"""Generate all the code for the test gen."""

import argparse
import os
import pathlib
import sys

import dev_scripts.codegen.generate_creation


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    error = dev_scripts.codegen.generate_creation.generate_and_write()
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
