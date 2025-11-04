from pathlib import Path
from typing import Final, List, Optional

import click
import os

from src.bazelize_deps import bazelize_deps, DetachedModeMetadata
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
If there are more than one input file, simply do -i path_to_file for each file.""",
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
@click.option(
    "--tags",
    "-t",
    required=False,
    multiple=True,
    help="Tags to add to the generated targets.",
)
@click.option(
    "--detached_build_files_mode",
    "-db",
    is_flag=True,
    help="""If set, the BUILD files will be detached from the package and stored separately.""",
)
@click.option(
    "--url_prefix",
    "-u",
    type=str,
    required=False,
    help="""The URL prefix of the uploaded http_archives.""",
)
@click.option(
    "--build_file_package",
    "-bp",
    type=str,
    required=False,
    help="""The package within which the build files will be dumped. Example: //third_party""",
)
@click.option(
    "--archives_file",
    "-af",
    type=click.Path(path_type=Path, dir_okay=False),
    required=False,
    help="""Path to the <name>.MODULE.bazel file containing the http_archives.""",
)
@click.option(
    "--build_files_dir",
    "-bf",
    type=click.Path(path_type=Path, file_okay=False),
    required=False,
    help="""Path to the build files if in detached mode.""",
)
def main(
    input_file: List[Path],
    modules_path: Path,
    delimiter: str,
    tags: List[str],
    detached_build_files_mode: bool,
    url_prefix: str,
    build_file_package: str,
    archives_file: Optional[Path],
    build_files_dir: Optional[Path],
):
    """Turns input deb packages into modules and dumps it in modules_path."""
    if delimiter not in {"~", "+"}:
        raise ValueError(
            f"Delimiter: {delimiter} is not allowed. Delimiter must be either ~ or +"
        )

    if detached_build_files_mode and (
        not url_prefix
        or not build_file_package
        or not archives_file
        or not build_files_dir
    ):
        raise ValueError(
            "--build_file_package, --url_prefix, --archives_file_path and --build_files_path are required when --detach_build_file is set."
        )

    input_files = [
        file if file.is_absolute() else Path(BAZEL_WORKSPACE_DIR_STR) / file
        for file in input_file
    ]

    for file in input_files:
        if not file.exists():
            raise ValueError(f"{file} does not exist")

    if archives_file and archives_file.exists():
        archives_file.unlink()

    detached_mode_metadata: None | DetachedModeMetadata = None
    if detached_build_files_mode:
        detached_mode_metadata = DetachedModeMetadata(
            url_prefix=url_prefix,
            build_file_package=build_file_package,
            archives_file=archives_file,
            build_files_dir=build_files_dir,
        )

    bazelize_deps(
        modules_path=_get_path(modules_path),
        input_package_metadatas=read_input_files(input_files=input_files),
        delimiter=delimiter,
        tags=tags,
        detached_mode_metadata=detached_mode_metadata,
    )


if __name__ == "__main__":
    main()
