"""Generate all the test data."""

import argparse
import os
import pathlib
import sys

import aas_core3_0_testgen.generate_json
import aas_core3_0_testgen.generate_rdf
import aas_core3_0_testgen.generate_xml


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))
    test_data_dir = this_path.parent.parent / "test_data"

    aas_core3_0_testgen.generate_json.generate(test_data_dir=test_data_dir)
    aas_core3_0_testgen.generate_rdf.generate(test_data_dir=test_data_dir)
    aas_core3_0_testgen.generate_xml.generate(test_data_dir=test_data_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
