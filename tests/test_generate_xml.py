# pylint: disable=missing-docstring
import difflib
import os.path
import pathlib
import tempfile
import unittest
from typing import List, Tuple
import xml.etree.ElementTree

import xmlschema
import aas_core_meta.v3

import aas_core3_0_testgen.generate_xml


class Test_against_recorded(unittest.TestCase):
    def test_that_it_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_as_str:
            tmp_dir = pathlib.Path(tmp_dir_as_str)

            aas_core3_0_testgen.generate_xml.generate(
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

            got_files = sorted(tmp_dir.glob("Xml/**/*.xml"))

            got_file_set = set(str(pth.relative_to(tmp_dir)) for pth in got_files)

            expected_files = sorted(test_data_dir.glob("Xml/**/*.xml"))

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

    def test_that_expected_conform_to_schema(self) -> None:
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

        schema_pth = test_data_dir / "schema.xsd"
        schema = xmlschema.XMLSchema(str(schema_pth))

        ok_files = sorted(
            test_data_dir.glob("Xml/ContainedInEnvironment/Expected/**/*.xml")
        )

        # NOTE (mristin, 2023-03-15):
        # We can not fight xmlschema. It seems that it doesn't work well with
        # UTF-32 code points in patterns.
        excluded_list = []  # type: List[pathlib.Path]

        excluded_list.extend(
            (
                test_data_dir
                / "Xml/ContainedInEnvironment/Expected"
                / "blob/contentTypeOverPatternExamples"
            ).glob("fuzzed*.xml")
        )
        excluded_list.extend(
            (
                test_data_dir
                / "Xml/ContainedInEnvironment/Expected"
                / "extension/OverValueExamples/String"
            ).glob("fuzzed*.xml")
        )
        excluded_list.extend(
            (
                test_data_dir
                / "Xml/ContainedInEnvironment/Expected"
                / "file/contentTypeOverPatternExamples"
            ).glob("fuzzed*.xml")
        )
        excluded_list.extend(
            (
                test_data_dir
                / "Xml/ContainedInEnvironment/Expected"
                / "property/OverValueExamples/String"
            ).glob("fuzzed*.xml")
        )
        excluded_list.extend(
            (
                test_data_dir
                / "Xml/ContainedInEnvironment/Expected"
                / "qualifier/OverValueExamples/String"
            ).glob("fuzzed*.xml")
        )
        excluded_list.extend(
            (
                test_data_dir
                / "Xml/ContainedInEnvironment/Expected"
                / "range/OverMinMaxExamples/String"
            ).glob("fuzzed*.xml")
        )
        excluded_list.extend(
            (
                test_data_dir
                / "Xml/ContainedInEnvironment/Expected"
                / "resource/contentTypeOverPatternExamples"
            ).glob("fuzzed*.xml")
        )

        excluded_set = set(excluded_list)

        for pth in ok_files:
            if pth in excluded_set:
                continue

            try:
                schema.validate(pth)
            except (
                xmlschema.validators.exceptions.XMLSchemaValidationError,
                xml.etree.ElementTree.ParseError,
            ) as err:
                raise AssertionError(
                    f"Failed to validate {pth} against {schema_pth}"
                ) from err


if __name__ == "__main__":
    unittest.main()
