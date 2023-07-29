from pathlib import Path
from typing import Final, Dict, List

import click
import json
import os

from dep_bazelizer_config import get_deb_packages_path, get_s3_config_file_path
from src.bazelize_deps import bazelize_deps
from src.read_input_files import read_input_files

BAZEL_WORKSPACE_DIR: Final = (
    os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    or os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
    or os.environ.get("TEST_TMPDIR")
)
MANDATORY_CONFIGS: Final = ["upload_bucket", "upload_url"]


def _get_s3_config(json_config_file: Path):
    if json_config_file.suffix != ".json":
        path_str = str(json_config_file)
        raise ValueError(f"The file '{path_str}' must be a .json file.")

    with open(json_config_file, encoding="utf-8") as json_config:
        s3_config = json.load(json_config)

    _verify_s3_config(s3_config)

    return s3_config


def _verify_s3_config(configs: Dict[str, str]):
    for mandatory_config in MANDATORY_CONFIGS:
        if mandatory_config not in configs:
            raise ValueError(f"missing mandatory config: {mandatory_config}.")


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option(
    "--registry_path",
    "-rp",
    type=click.Path(path_type=Path, file_okay=False),
    required=False,
    default=Path().joinpath(BAZEL_WORKSPACE_DIR, "registry"),
    help="""The path to the directory where the local registry will reside.
If path is relative, it is assumed to be relative to the workspace dir.""",
)
@click.option(
    "--input_file",
    "-if",
    type=click.Path(path_type=Path, dir_okay=False),
    required=False,
    default=[Path(get_deb_packages_path())],
    multiple=True,
    help="""The path to the input file containing the input debian packages.
If path is relative, it is assumed to be relative to the workspace dir. 
If there are more than one input file, simply do -if path_to_file for each file.""",
)
@click.option(
    "--s3_config_file",
    "-cf",
    type=click.Path(path_type=Path, dir_okay=False),
    required=False,
    default=Path(get_s3_config_file_path()),
    help="""The path to the s3 config file containing the configs like bucket, url, etc.
If path is relative, it is assumed to be relative to the workspace dir""",
)
def main(registry_path: Path, input_file: List[Path], s3_config_file: Path):
    """Turns input deb packages into modules referenced by a local registry."""
    if not registry_path.is_absolute():
        registry_path = Path(BAZEL_WORKSPACE_DIR) / registry_path

    if not s3_config_file.is_absolute():
        s3_config_file = Path(BAZEL_WORKSPACE_DIR) / s3_config_file

    input_files = [
        file if file.is_absolute() else Path(BAZEL_WORKSPACE_DIR) / file
        for file in input_file
    ]

    for file in input_files:
        if not file.exists():
            input_file_str = str(file)
            raise ValueError(f"{input_file_str} does not exist")

    bazelize_deps(
        registry_path=registry_path,
        s3_config=_get_s3_config(s3_config_file),
        input_package_metadatas=read_input_files(
            registry_path=registry_path, input_files=input_files
        ),
    )


if __name__ == "__main__":
    main()
