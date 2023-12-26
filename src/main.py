from pathlib import Path
from typing import Final, List

import click
import os

from src.bazelize_deps import bazelize_deps
from src.read_input_files import read_input_files
from src.storage import create_storage

BAZEL_WORKSPACE_DIR: Final = (
    os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    or os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
    or os.environ.get("TEST_TMPDIR")
)

BAZEL_WORKSPACE_DIR_STR: Final = BAZEL_WORKSPACE_DIR if BAZEL_WORKSPACE_DIR else ""

@click.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "--registry_path",
    "-r",
    type=click.Path(path_type=Path, file_okay=False),
    required=False,
    default=Path().joinpath(BAZEL_WORKSPACE_DIR_STR, "registry"),
    help="""The path to the directory where the local registry will reside.
If path is relative, it is assumed to be relative to the workspace dir.""",
)
@click.option(
    "--input_file",
    "-i",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    multiple=True,
    help="""The path to the input file containing the input debian packages.
If path is relative, it is assumed to be relative to the workspace dir. 
If there are more than one input file, simply do -if path_to_file for each file.""",
)
@click.option(
    "--config_file",
    "-c",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="""The path to the s3 config file containing the configs like bucket, url, etc.
If path is relative, it is assumed to be relative to the workspace dir""",
)
def main(registry_path: Path, input_file: List[Path], config_file: Path):
    """Turns input deb packages into modules referenced by a local registry."""
    if not registry_path.is_absolute():
        registry_path = Path(BAZEL_WORKSPACE_DIR_STR) / registry_path

    if not config_file.is_absolute():
        config_file = Path(BAZEL_WORKSPACE_DIR_STR) / config_file

    input_files = [
        file if file.is_absolute() else Path(BAZEL_WORKSPACE_DIR_STR) / file
        for file in input_file
    ]

    for file in input_files:
        if not file.exists():
            input_file_str = str(file)
            raise ValueError(f"{input_file_str} does not exist")

    bazelize_deps(
        registry_path=registry_path,
        storage=create_storage(config_file),
        input_package_metadatas=read_input_files(
            registry_path=registry_path, input_files=input_files
        ),
    )


if __name__ == "__main__":
    main()
