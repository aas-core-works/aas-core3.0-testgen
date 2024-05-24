"""Generate all the code for the test gen."""

import argparse
import os
import pathlib
import sys

import dev_scripts.codegen.generate_creation
import dev_scripts.codegen.generate_wrapping
import dev_scripts.codegen.generate_preserialization
import dev_scripts.codegen.generate_abstract_fixing


def main() -> int:
    """Execute the main routine."""
    repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--codegened_dir",
        help="path to the directory containing the generated code",
        default=str(repo_dir / "aas_core3_0_testgen" / "codegened"),
    )
    args = parser.parse_args()

    model_path = pathlib.Path(args.model_path)
    codegened_dir = pathlib.Path(args.codegened_dir)

    error = dev_scripts.codegen.generate_creation.generate_and_write(
        model_path=model_path, codegened_dir=codegened_dir
    )
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    error = dev_scripts.codegen.generate_wrapping.generate_and_write(
        model_path=model_path, codegened_dir=codegened_dir
    )
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    error = dev_scripts.codegen.generate_preserialization.generate_and_write(
        model_path=model_path, codegened_dir=codegened_dir
    )
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    error = dev_scripts.codegen.generate_abstract_fixing.generate_and_write(
        model_path=model_path, codegened_dir=codegened_dir
    )
    if error is not None:
        print(f"Failed to generate creation: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
