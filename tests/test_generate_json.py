# pylint: disable=missing-docstring
import difflib
import json
import os.path
import pathlib
import tempfile
import unittest
from typing import List, Tuple, Optional

import aas_core_meta.v3
import jsonschema

import aas_core3_0_testgen.generate_json


class Test_against_recorded(unittest.TestCase):
    def test_that_it_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_as_str:
            tmp_dir = pathlib.Path(tmp_dir_as_str)

            aas_core3_0_testgen.generate_json.generate(
                model_path=pathlib.Path(aas_core_meta.v3.__file__),
                test_data_dir=tmp_dir,
            )

            repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent
            test_data_dir = repo_root / "test_data"
            if not test_data_dir.exists():
                raise FileNotFoundError(
                    f"Directory with the test data does not exist: {test_data_dir}"
                )

            if not test_data_dir.is_dir():
                raise NotADirectoryError(
                    f"The test data dir is not a directory: {test_data_dir}"
                )

            got_files = sorted(tmp_dir.glob("Json/**/*.json"))

            got_file_set = set(str(pth.relative_to(tmp_dir)) for pth in got_files)

            expected_files = sorted(test_data_dir.glob("Json/**/*.json"))

            expected_file_set = set(
                str(pth.relative_to(test_data_dir)) for pth in expected_files
            )

            if got_file_set != expected_file_set:
                only_in_got = sorted(got_file_set.difference(expected_file_set))
                only_in_expected = sorted(expected_file_set.difference(got_file_set))

                parts = []  # type: List[str]

                if len(only_in_got) > 0:
                    only_in_got_str = ",\n".join(only_in_got)
                    parts.append(
                        f"File(s) in temporary directory, "
                        f"but not in {test_data_dir}: {only_in_got_str}"
                    )

                if len(only_in_expected) > 0:
                    only_in_expected_str = ",\n".join(only_in_expected)
                    parts.append(
                        f"File(s) in {test_data_dir}directory, "
                        f"but not in the temporary directory: {only_in_expected_str}"
                    )

                parts.insert(
                    0,
                    "There are differences in generated files and the expected files.",
                )

                raise AssertionError("\n\n".join(parts))

            paths_diffs = []  # type: List[Tuple[pathlib.Path, str]]
            for pth in got_files:
                relative_pth = pth.relative_to(tmp_dir)

                expected_pth = test_data_dir / relative_pth

                got_text = pth.read_text(encoding="utf-8")
                expected_text = expected_pth.read_text(encoding="utf-8")

                if got_text != expected_text:
                    diffs = difflib.ndiff(
                        got_text.splitlines(), expected_text.splitlines()
                    )

                    paths_diffs.append((relative_pth, "\n\n".join(diffs)))

            if len(paths_diffs) > 0:
                parts = [
                    "There are differences between the generated and "
                    "the expected examples."
                ]

                for pth, diff in paths_diffs:
                    parts.append(f"In {pth}:\n{diff}")

                raise AssertionError("\n\n".join(parts))

    def test_schema_validation_against_cases(self) -> None:
        repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent
        test_data_dir = repo_root / "test_data"
        if not test_data_dir.exists():
            raise FileNotFoundError(
                f"Directory with the test data does not exist: {test_data_dir}"
            )

        if not test_data_dir.is_dir():
            raise NotADirectoryError(
                f"The test data dir is not a directory: {test_data_dir}"
            )

        schema_pth = test_data_dir / "schema.json"
        with schema_pth.open("rt") as fid:
            schema = json.load(fid)

        # NOTE (mristin):
        # We can only validate against the environment as JSON schema expects only
        # environment at the root.
        ok_files = sorted(
            test_data_dir.glob("Json/ContainedInEnvironment/Expected/**/*.json")
        )

        case_subpaths = (
            pathlib.Path("Unserializable/TypeViolation"),
            pathlib.Path("Invalid/PatternViolation"),
            pathlib.Path("Unserializable/RequiredViolation"),
            pathlib.Path("Invalid/MinLengthViolation"),
            pathlib.Path("Invalid/MaxLengthViolation"),
            pathlib.Path("Unserializable/EnumViolation"),
        )

        schema_violation_files = []  # type: List[pathlib.Path]
        for case_subpath in case_subpaths:
            # NOTE (mristin):
            # We can only validate against the environment as JSON schema expects only
            # environment at the root.
            glob_pattern = (
                f"Json/ContainedInEnvironment/Unexpected/" f"{case_subpath}/**/*.json"
            )

            case_violation_files = list(test_data_dir.glob(glob_pattern))
            if len(case_violation_files) == 0:
                raise AssertionError(
                    f"Unexpected no files in {test_data_dir} matching {glob_pattern}"
                )

            schema_violation_files.extend(case_violation_files)

        schema_violation_files.sort()

        for pth in ok_files:
            try:
                with pth.open("rt") as fid:
                    jsonable = json.load(fid)

                jsonschema.validate(instance=jsonable, schema=schema)
            except Exception as exception:
                raise AssertionError(
                    f"Failed to validate {pth} against {schema_pth}"
                ) from exception

        for pth in schema_violation_files:
            with pth.open("rt") as fid:
                jsonable = json.load(fid)

            observed_error = None  # type: Optional[jsonschema.ValidationError]
            try:
                jsonschema.validate(instance=jsonable, schema=schema)
            except jsonschema.ValidationError as error:
                observed_error = error

            assert (
                observed_error is not None
            ), f"Expected a validation error for {pth}, but got none"


if __name__ == "__main__":
    unittest.main()
