"""Generate all the code for the test gen."""

import argparse
import sys

import dev_scripts.codegen.generate_creation
import dev_scripts.codegen.generate_wrapping
import dev_scripts.codegen.generate_preserialization
import dev_scripts.codegen.generate_abstract_fixing


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    error = dev_scripts.codegen.generate_creation.generate_and_write()
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    error = dev_scripts.codegen.generate_wrapping.generate_and_write()
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    error = dev_scripts.codegen.generate_preserialization.generate_and_write()
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    error = dev_scripts.codegen.generate_abstract_fixing.generate_and_write()
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
