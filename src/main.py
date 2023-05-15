from typing import Final
from pathlib import Path

import click
import os

from src.bazelize_deps import bazelize_deps
from src.read_input_file import read_input_file

BAZEL_WORKSPACE_DIR: Final = os.environ.get("BUILD_WORKSPACE_DIRECTORY") or os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR") or os.environ.get("TEST_TMPDIR")

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option("--modules_path",
               "-mp", 
               type=click.Path(path_type=Path, file_okay=False), 
               required=False,
               default=Path().joinpath(BAZEL_WORKSPACE_DIR, "modules"),
               help="The path to the directory where the local modules will reside. If path is relative, it is assumed to be relative to the workspace dir"
            )
@click.option("--registry_path",
               "-rp", 
               type=click.Path(path_type=Path, file_okay=False), 
               required=False,
               default=Path().joinpath(BAZEL_WORKSPACE_DIR, "registry"),
               help="The path to the directory where the local registry will reside. If path is relative, it is assumed to be relative to the workspace dir"
            )
@click.option("--input_file",
               "-if", 
               type=click.Path(path_type=Path, dir_okay=False), 
               required=True,
               help="The path to the input file containing the input debian packages. If path is relative, it is assumed to be relative to the workspace dir"
            )
def main(modules_path: Path, registry_path: Path, input_file: Path):
    """Turns input deb packages into modules referenced by a local registry."""
    
    if not modules_path.is_absolute():
        modules_path = Path(BAZEL_WORKSPACE_DIR) / modules_path
    
    if not registry_path.is_absolute():
        registry_path = Path(BAZEL_WORKSPACE_DIR) / registry_path
    
    if not input_file.is_absolute():
        input_file = Path(BAZEL_WORKSPACE_DIR) / input_file
    
    if not input_file.exists():
        input_file_str = str(input_file)
        raise ValueError(f"{input_file_str} does not exist")
            
    modules_path.mkdir(exist_ok=True, parents=True)
    bazelize_deps(
        modules_path=modules_path,
        registry_path=registry_path,
        input_package_metadatas=read_input_file(registry_path=registry_path, input_file = input_file)
    )

if __name__ == "__main__":
    main()