"""Generate all the test data."""

import argparse
import pathlib
import sys

import aas_core3_0_testgen.generate_json
import aas_core3_0_testgen.generate_rdf
import aas_core3_0_testgen.generate_xml


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--test_data_dir",
        help="path to the directory where the generated data resides",
        required=True,
    )
    args = parser.parse_args()

    model_path = pathlib.Path(args.model_path)
    test_data_dir = pathlib.Path(args.test_data_dir)

    aas_core3_0_testgen.generate_json.generate(
        model_path=model_path, test_data_dir=test_data_dir
    )
    aas_core3_0_testgen.generate_rdf.generate(
        model_path=model_path, test_data_dir=test_data_dir
    )
    aas_core3_0_testgen.generate_xml.generate(
        model_path=model_path, test_data_dir=test_data_dir
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
