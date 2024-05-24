"""
Update everything in this project to the latest aas-core-meta.

Git is expected to be installed.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Optional, List, Callable, AnyStr, Sequence

# NOTE (mristin):
# We import the meta-model module here since we do not run this script to generate
# the test data according to an arbitrary model, but to the concrete one as we pinned
# it in ``setup.py``. We expect the files in ``test_data/`` directory to correspond to
# exactly that meta-model version.
import aas_core_meta.v3

AAS_CORE_META_DEPENDENCY_RE = re.compile(
    r"aas-core-meta@git\+https://github.com/aas-core-works/aas-core-meta@([a-fA-F0-9]+)#egg=aas-core-meta"
)

AAS_CORE_CODEGEN_DEPENDENCY_RE = re.compile(
    r"aas-core-codegen@git\+https://github.com/aas-core-works/aas-core-codegen@([a-fA-F0-9]+)#egg=aas-core-codegen"
)


def _make_sure_no_changed_files(
    repo_dir: pathlib.Path, expected_branch: str
) -> Optional[int]:
    """
    Make sure that no files are modified in the given repository.

    Return exit code if something is unexpected.
    """
    diff_name_status = subprocess.check_output(
        ["git", "diff", "--name-status", expected_branch],
        cwd=str(repo_dir),
        encoding="utf-8",
    ).strip()

    if len(diff_name_status.splitlines()) > 0:
        print(
            f"The following files are modified "
            f"compared to branch {expected_branch!r} in {repo_dir}:\n"
            f"{diff_name_status}\n"
            f"\n"
            f"Please stash the changes first before you update to aas-core-meta.",
            file=sys.stderr,
        )
        return 1

    return None


def _update_setup_py(
    our_repo: pathlib.Path, aas_core_meta_revision: str, aas_core_codegen_revision: str
) -> None:
    """Update the aas-core-meta in setup.py."""
    setup_py = our_repo / "setup.py"
    text = setup_py.read_text(encoding="utf-8")

    aas_core_meta_dependency = (
        f"aas-core-meta@git+https://github.com/aas-core-works/aas-core-meta"
        f"@{aas_core_meta_revision}#egg=aas-core-meta"
    )

    text = re.sub(AAS_CORE_META_DEPENDENCY_RE, aas_core_meta_dependency, text)

    aas_core_codegen_dependency = (
        f"aas-core-codegen@git+https://github.com/aas-core-works/aas-core-codegen"
        f"@{aas_core_codegen_revision}#egg=aas-core-codegen"
    )

    text = re.sub(AAS_CORE_CODEGEN_DEPENDENCY_RE, aas_core_codegen_dependency, text)

    setup_py.write_text(text, encoding="utf-8")


def _uninstall_and_install_aas_core_meta(
    our_repo: pathlib.Path, aas_core_meta_revision: str
) -> None:
    """Uninstall and install the latest aas-core-meta in the virtual environment."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "uninstall", "-y", "aas-core-meta"],
        cwd=str(our_repo),
    )

    aas_core_meta_dependency = (
        f"aas-core-meta@git+https://github.com/aas-core-works/aas-core-meta"
        f"@{aas_core_meta_revision}#egg=aas-core-meta"
    )

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", aas_core_meta_dependency],
        cwd=str(our_repo),
    )


def _uninstall_and_install_aas_core_codegen(
    our_repo: pathlib.Path, aas_core_codegen_revision: str
) -> None:
    """Uninstall and install the latest aas-core-codegen in the virtual environment."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "uninstall", "-y", "aas-core-codegen"],
        cwd=str(our_repo),
    )

    aas_core_codegen_dependency = (
        f"aas-core-codegen@git+https://github.com/aas-core-works/aas-core-codegen"
        f"@{aas_core_codegen_revision}#egg=aas-core-codegen"
    )

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", aas_core_codegen_dependency],
        cwd=str(our_repo),
    )


def _copy_python_sdk_and_schemas_from_aas_core_codegen(
    aas_core_codegen_repo: pathlib.Path,
    our_repo: pathlib.Path,
    aas_core_codegen_revision: str,
) -> None:
    """Copy the generated Python SDK from aas-core-codegen's test data."""
    source_dir = (
        aas_core_codegen_repo
        / "test_data/python/test_main/aas_core_meta.v3/expected_output"
    )

    target_dir = our_repo / "aas_core3"

    for pth in source_dir.glob("*.py"):
        tgt_pth = target_dir / pth.name
        shutil.copy(pth, tgt_pth)

    init_py = target_dir / "__init__.py"

    text = f'''\
"""
Provide Python SDK as copied from aas-core-codegen test data.

This copy is necessary so that we can decouple from ``aas-core*-python`` repository.

The revision of aas-core-codegen was: {aas_core_codegen_revision}
"""
'''
    init_py.write_text(text, encoding="utf-8")

    shutil.copy(
        aas_core_codegen_repo
        / "test_data/jsonschema/test_main/aas_core_meta.v3/expected_output/schema.json",
        our_repo / "test_data/schema.json",
    )

    shutil.copy(
        aas_core_codegen_repo
        / "test_data/xsd/test_main/aas_core_meta.v3/expected_output/schema.xsd",
        our_repo / "test_data/schema.xsd",
    )


def _run_in_parallel(
    calls: Sequence[Callable[[], subprocess.Popen[AnyStr]]],
    on_status_update: Callable[[int], None],
) -> Optional[int]:
    """
    Run the given scripts in parallel.

    Return an error code, if any.
    """
    procs = []  # type: List[subprocess.Popen[AnyStr]]

    try:
        for call in calls:
            proc = call()
            procs.append(proc)

        failure = False
        remaining_procs = sum(1 for proc in procs if proc.returncode is None)

        next_print = time.time() + 15
        while remaining_procs > 0:
            if time.time() > next_print:
                on_status_update(remaining_procs)
                next_print = time.time() + 15

            time.sleep(1)

            for proc in procs:
                proc.poll()

                if proc.returncode is not None:
                    if proc.returncode != 0:
                        failure = True

            if failure:
                print(
                    "One or more processes failed. Terminating all the processes...",
                    file=sys.stderr,
                )
                for proc in procs:
                    proc.terminate()

                print("Terminated all the processes.", file=sys.stderr)
                return 1

            for proc in procs:
                proc.poll()

            remaining_procs = sum(1 for proc in procs if proc.returncode is None)

        return None
    finally:
        for proc in procs:
            if proc.returncode is None:
                proc.terminate()


def _generate_code(our_repo: pathlib.Path) -> Optional[int]:
    """Run the code generation of our scripts."""
    dev_scripts_codegen_dir = our_repo / "dev_scripts/codegen"
    scripts = sorted(
        pth
        for pth in dev_scripts_codegen_dir.glob("generate_*.py")
        if pth.name != "generate_all.py"
    )

    cmds = [
        [
            sys.executable,
            str(pth.relative_to(our_repo)),
            "--model_path",
            str(pathlib.Path(aas_core_meta.v3.__file__).relative_to(our_repo)),
            "--codegened_dir",
            "aas_core3_0_testgen/codegened",
        ]
        for pth in scripts
    ]  # type: Sequence[Sequence[str]]

    # pylint: disable=consider-using-with
    calls = [
        lambda cmd=a_cmd, cwd=our_repo: subprocess.Popen(  # type: ignore
            cmd,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )
        for a_cmd in cmds
    ]  # type: Sequence[Callable[[], subprocess.Popen[str]]]
    # pylint: enable=consider-using-with

    cmds_joined = "\n".join(" ".join(cmd) for cmd in cmds)
    print(f"Starting to run codegen scripts:\n{cmds_joined}")
    start = time.perf_counter()

    exit_code = _run_in_parallel(
        calls=calls,
        on_status_update=(
            lambda remaining: print(
                f"There are {remaining} codegen script(s) still running..."
            )
        ),
    )
    if exit_code is not None:
        return exit_code

    duration = time.perf_counter() - start
    print(f"Generating the code took: {duration:.2f} seconds.")

    return None


def _reformat_code(our_repo: pathlib.Path) -> None:
    """Reformat the generated code."""
    precommit_script = our_repo / "continuous_integration/precommit.py"
    subprocess.check_call(
        [sys.executable, str(precommit_script), "--overwrite", "--select", "reformat"],
        cwd=our_repo,
    )


def _run_tests_in_parallel(our_repo: pathlib.Path) -> Optional[int]:
    """
    Run the unit tests in parallel.

    Return an error code, if any.
    """
    test_qualnames = [
        f"tests.{pth.stem}"
        for pth in (our_repo / "tests").glob("test_*.py")
        if (
            pth.is_file()
            and not pth.name.startswith("__")
            and not pth.name.startswith(".")
        )
    ]

    # pylint: disable=consider-using-with
    # fmt: off
    calls = [
        lambda a_test_qualname=test_qualname, cwd=our_repo:  # type: ignore
        subprocess.Popen(
            [sys.executable, "-m", "unittest", a_test_qualname],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )
        for test_qualname in test_qualnames
    ]  # type: Sequence[Callable[[], subprocess.Popen[str]]]
    # fmt: on
    # pylint: enable=consider-using-with

    test_qualnames_joined = ",\n".join(
        str(test_qualname) for test_qualname in test_qualnames
    )
    print(f"Starting to run unit tests:\n{test_qualnames_joined}")
    start = time.perf_counter()

    exit_code = _run_in_parallel(
        calls=calls,
        on_status_update=(
            lambda remaining: print(
                f"There are {remaining} unit test(s) still running..."
            )
        ),
    )
    if exit_code is not None:
        return exit_code

    duration = time.perf_counter() - start
    print(f"Running the unit tests took: {duration:.2f} seconds.")

    return None


def _generate_test_data(our_repo: pathlib.Path) -> Optional[int]:
    """
    Run generate scripts in parallel.

    Return an error code, if any.
    """
    # NOTE (mristin, 2024-04-16):
    # We delete first the generated test data since the meta-model influences also
    # the directory structures.
    #
    # For example, required violations will change when a field is made optional.
    test_data_dir = our_repo / "test_data"
    shutil.rmtree(test_data_dir / "Json")
    shutil.rmtree(test_data_dir / "Rdf")
    shutil.rmtree(test_data_dir / "Xml")

    scripts = [
        our_repo / "aas_core3_0_testgen" / name
        for name in ("generate_json.py", "generate_rdf.py", "generate_xml.py")
    ]

    # pylint: disable=consider-using-with
    calls = [
        lambda a_pth=script, cwd=our_repo: subprocess.Popen(
            [
                sys.executable,
                str(a_pth),
                "--model_path",
                aas_core_meta.v3.__file__,
                "--test_data_dir",
                test_data_dir,
            ],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )
        for script in scripts
    ]
    # pylint: enable=consider-using-with

    scripts_joined = ",\n".join(str(script) for script in scripts)
    print(f"Starting to run:\n{scripts_joined}")
    start = time.perf_counter()

    exit_code = _run_in_parallel(
        calls=calls,
        on_status_update=(
            lambda remaining: print(
                f"There are {remaining} generation script(s) still running..."
            )
        ),
    )
    if exit_code is not None:
        return exit_code

    duration = time.perf_counter() - start
    print(f"Generating the data took: {duration:.2f} seconds.")

    return None


def _create_branch_commit_and_push(
    our_repo: pathlib.Path, aas_core_meta_revision: str, aas_core_codegen_revision: str
) -> None:
    """Create a feature branch, commit the changes and push it."""
    branch = (
        f"Update-to-aas-core-meta-{aas_core_meta_revision}-"
        f"and-codegen-{aas_core_codegen_revision}"
    )
    print(f"Creating the branch {branch!r}...")
    subprocess.check_call(["git", "checkout", "-b", branch], cwd=our_repo)

    print("Adding files...")
    subprocess.check_call(["git", "add", "."], cwd=our_repo)

    # pylint: disable=line-too-long
    message = f"""\
Update to aas-core-meta, codegen {aas_core_meta_revision}, {aas_core_codegen_revision}

We update the development requirements to and re-generate everything
with:
* [aas-core-meta {aas_core_meta_revision}], and
* [aas-core-codegen {aas_core_codegen_revision}].

[aas-core-meta {aas_core_meta_revision}]: https://github.com/aas-core-works/aas-core-meta/commit/{aas_core_meta_revision}
[aas-core-codegen {aas_core_codegen_revision}]: https://github.com/aas-core-works/aas-core-codegen/commit/{aas_core_codegen_revision}"""
    # pylint: enable=line-too-long

    print("Committing...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = pathlib.Path(tmp_dir) / "commit-message.txt"
        tmp_file.write_text(message, encoding="utf-8")

        subprocess.check_call(["git", "commit", "--file", str(tmp_file)], cwd=our_repo)

    print(f"Pushing to remote {branch}...")
    subprocess.check_call(["git", "push", "-u"], cwd=our_repo)


def main() -> int:
    """Execute the main routine."""
    this_path = pathlib.Path(os.path.realpath(__file__))
    our_repo = this_path.parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aas_core_meta_repo",
        help="path to the aas-core-meta repository",
        default=str(our_repo.parent / "aas-core-meta"),
    )
    parser.add_argument(
        "--expected_aas_core_meta_branch",
        help="Git branch expected in the aas-core-meta repository",
        default="main",
    )
    parser.add_argument(
        "--aas_core_codegen_repo",
        help="path to the aas-core-codegen repository",
        default=str(our_repo.parent / "aas-core-codegen"),
    )
    parser.add_argument(
        "--expected_aas_core_codegen_branch",
        help="Git branch expected in the aas-core-meta repository",
        default="main",
    )
    parser.add_argument(
        "--expected_our_branch",
        help="Git branch expected in this repository",
        default="main",
    )

    args = parser.parse_args()

    aas_core_meta_repo = pathlib.Path(args.aas_core_meta_repo)
    expected_aas_core_meta_branch = str(args.expected_aas_core_meta_branch)

    aas_core_codegen_repo = pathlib.Path(args.aas_core_codegen_repo)
    expected_aas_core_codegen_branch = str(args.expected_aas_core_codegen_branch)

    expected_our_branch = str(args.expected_our_branch)

    # region aas-core-meta repo

    if not aas_core_meta_repo.exists():
        print(
            f"--aas_core_meta_repo does not exist: {aas_core_meta_repo}",
            file=sys.stderr,
        )
        return 1

    if not aas_core_meta_repo.is_dir():
        print(
            f"--aas_core_meta_repo is not a directory: {aas_core_meta_repo}",
            file=sys.stderr,
        )
        return 1

    aas_core_meta_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(aas_core_meta_repo),
        encoding="utf-8",
    ).strip()
    if aas_core_meta_branch != expected_aas_core_meta_branch:
        print(
            f"--expected_aas_core_meta_branch is {expected_aas_core_meta_branch}, "
            f"but got {aas_core_meta_branch} "
            f"in --aas_core_meta_repo: {aas_core_meta_repo}",
            file=sys.stderr,
        )
        return 1

    aas_core_meta_revision = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(aas_core_meta_repo),
        encoding="utf-8",
    ).strip()

    # endregion

    # region aas-core-codegen repo

    if not aas_core_codegen_repo.exists():
        print(
            f"--aas_core_codegen_repo does not exist: {aas_core_codegen_repo}",
            file=sys.stderr,
        )
        return 1

    if not aas_core_codegen_repo.is_dir():
        print(
            f"--aas_core_codegen_repo is not a directory: {aas_core_codegen_repo}",
            file=sys.stderr,
        )
        return 1

    aas_core_codegen_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(aas_core_codegen_repo),
        encoding="utf-8",
    ).strip()
    if aas_core_codegen_branch != expected_aas_core_codegen_branch:
        print(
            f"--expected_aas_core_codegen_branch is {expected_aas_core_codegen_branch}, "
            f"but got {aas_core_codegen_branch} "
            f"in --aas_core_codegen_repo: {aas_core_codegen_repo}",
            file=sys.stderr,
        )
        return 1

    aas_core_codegen_revision = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(aas_core_codegen_repo),
        encoding="utf-8",
    ).strip()

    # endregion

    # region Our repo

    our_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(our_repo),
        encoding="utf-8",
    ).strip()
    if our_branch != expected_our_branch:
        print(
            f"--expected_our_branch is {expected_our_branch}, "
            f"but got {our_branch} in: {our_repo}",
            file=sys.stderr,
        )
        return 1

    # endregion

    for repo_dir, expected_branch in [
        (our_repo, expected_our_branch),
        (aas_core_meta_repo, expected_aas_core_meta_branch),
        (aas_core_codegen_repo, expected_aas_core_codegen_branch),
    ]:
        exit_code = _make_sure_no_changed_files(
            repo_dir=repo_dir, expected_branch=expected_branch
        )
        if exit_code is not None:
            return exit_code

    _update_setup_py(
        our_repo=our_repo,
        aas_core_meta_revision=aas_core_meta_revision,
        aas_core_codegen_revision=aas_core_codegen_revision,
    )

    _uninstall_and_install_aas_core_meta(
        our_repo=our_repo, aas_core_meta_revision=aas_core_meta_revision
    )

    _uninstall_and_install_aas_core_codegen(
        our_repo=our_repo, aas_core_codegen_revision=aas_core_codegen_revision
    )

    _copy_python_sdk_and_schemas_from_aas_core_codegen(
        aas_core_codegen_repo=aas_core_codegen_repo,
        our_repo=our_repo,
        aas_core_codegen_revision=aas_core_codegen_revision,
    )

    exit_code = _generate_code(our_repo=our_repo)
    if exit_code is not None:
        return exit_code

    _reformat_code(our_repo=our_repo)

    exit_code = _generate_test_data(our_repo=our_repo)
    if exit_code is not None:
        return exit_code

    exit_code = _run_tests_in_parallel(our_repo=our_repo)
    if exit_code is not None:
        return exit_code

    _create_branch_commit_and_push(
        our_repo=our_repo,
        aas_core_meta_revision=aas_core_meta_revision,
        aas_core_codegen_revision=aas_core_codegen_revision,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
