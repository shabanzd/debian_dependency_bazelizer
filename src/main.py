from typing import Final, Set
from pathlib import Path

import click
import os

from src.bazelize_deps import bazelize_deps
from src.package import PackageMetadata
from src.get_package_version import get_package_version

BAZEL_WORKSPACE_DIR: Final = os.environ["BUILD_WORKSPACE_DIRECTORY"]

def _get_package_metadata(registry_path: Path, pinned_package: str) -> PackageMetadata:
    if pinned_package.count(":") != 1 or pinned_package.count("=") > 1:
        raise ValueError("Entry has unexpected format, expected format: name:arch=version or name:arch")
    
    # entries format: name:arch=version
    name, arch_version = pinned_package.split(":")
    version = ""
    arch = arch_version

    if "=" in arch_version:
        arch, version = arch_version.split("=")
    
    if not version:
        version = get_package_version(registry_path=registry_path, name=name, arch=arch)

    return PackageMetadata(name=name, arch=arch, version=version)

def _get_input_package_metadatas(registry_path: Path, input_file: Path) -> Set[PackageMetadata]:
    with open(input_file, "r") as input_file:
        entries = set(input_file.read().splitlines())
    
    return {_get_package_metadata(registry_path=registry_path, pinned_package=entry) for entry in entries if entry and not entry.startswith("#")}
   
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
    modules_path.mkdir(exist_ok=True)
    bazelize_deps(
        modules_path=modules_path, 
        registry_path=registry_path, 
        input_package_metadatas=_get_input_package_metadatas(registry_path=registry_path, input_file = input_file)
    )

if __name__ == "__main__":
    main()