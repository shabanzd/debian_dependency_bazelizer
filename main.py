from pathlib import Path
from typing import Final, List

import click
import os

from src.bazelize_deps import bazelize_deps
from src.read_input_files import read_input_files

BAZEL_WORKSPACE_DIR: Final = (
    os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    or os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
    or os.environ.get("TEST_TMPDIR")
)

BAZEL_WORKSPACE_DIR_STR: Final = BAZEL_WORKSPACE_DIR if BAZEL_WORKSPACE_DIR else ""

def _get_path(path: Path) -> Path:
    return path if path.is_absolute() else Path(BAZEL_WORKSPACE_DIR_STR) / path

@click.command(context_settings={"ignore_unknown_options": True})
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
    "--modules_path",
    "-m",
    type=click.Path(path_type=Path, dir_okay=True, file_okay=False),
    required=True,
    help="""The path to dump the modules to. 
    If path is relative, it is assumed to be relative to the workspace dir.""",
)
@click.option(
    "--delimiter",
    "-d",
    required=False,
    default="~",
    help="""Starting bazel 7.3, modules can have a ~ delimiter or a + delimiter.""",
)
def main(input_file: List[Path], modules_path: Path, delimiter: str):
    """Turns input deb packages into modules and dumps it in modules_path."""
    if delimiter not in {"~", "+"}:
        raise ValueError(f"Delimiter: {delimiter} is not allowed. Delimiter must be either ~ or +")
        
    input_files = [
        file if file.is_absolute() else Path(BAZEL_WORKSPACE_DIR_STR) / file
        for file in input_file
    ]

    for file in input_files:
        if not file.exists():
            input_file_str = str(file)
            raise ValueError(f"{input_file_str} does not exist")

    bazelize_deps(
        modules_path=_get_path(modules_path),
        input_package_metadatas=read_input_files(input_files=input_files),
        delimiter=delimiter,
    )


if __name__ == "__main__":
    main()
