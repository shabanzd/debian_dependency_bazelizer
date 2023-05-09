from typing import Final
from pathlib import Path

import click
import os

from src.bazelize_deps import bazelize_deps
from src.read_input_file import read_input_file

BAZEL_WORKSPACE_DIR: Final = os.environ["BUILD_WORKSPACE_DIRECTORY"]

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option("--modules_path",
               "-mp", 
               type=click.Path(path_type=Path, file_okay=False), 
               required=False,
               default=Path().joinpath(BAZEL_WORKSPACE_DIR, "modules"),
               help="The path to the directory where the local modules will reside"
            )
@click.option("--registry_path",
               "-rp", 
               type=click.Path(path_type=Path, file_okay=False), 
               required=False,
               default=Path().joinpath(BAZEL_WORKSPACE_DIR, "registry"),
               help="The path to the directory where the local registry will reside"
            )
@click.option("--input_file",
               "-ip", 
               type=click.Path(path_type=Path, dir_okay=False, exists=True), 
               required=True,
               help="The path to the input file containing the input debian packages"
            )
def main(modules_path: Path, registry_path: Path, input_file: Path):
    """Turns input deb packages into modules referenced by a local registry."""
    modules_path.mkdir(exist_ok=True)
    bazelize_deps(
        modules_path=modules_path,
        registry_path=registry_path,
        input_package_metadatas=read_input_file(registry_path=registry_path, input_file = input_file)
    )

if __name__ == "__main__":
    main()