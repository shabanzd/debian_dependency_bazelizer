from typing import Final, Set
from pathlib import Path

import os

from create_deb_package import create_deb_package
from package import PackageMetadata
from get_package_version import get_package_version
from registry import find_package_in_registry
from writers import write_build_file, write_module_file

BAZEL_WORKSPACE_DIR: Final = os.environ["BUILD_WORKSPACE_DIRECTORY"]
DEB_PACKAGE_IN: Final = Path().joinpath(
    BAZEL_WORKSPACE_DIR, "src", "deb_packages.in"
)
MODULES_DIR : Final = Path().joinpath(BAZEL_WORKSPACE_DIR, "modules")


def _get_package_metadata(pinned_package: str) -> PackageMetadata:
    if pinned_package.count(":") != 1 or pinned_package.count("=") > 1:
        raise ValueError("Entry has unexpected format, expected format: name:arch=version or name:arch")
    
    # entries format: name:arch=version
    name, arch_version = pinned_package.split(":")
    version = ""
    arch = arch_version

    if "=" in arch_version:
        arch, version = arch_version.split("=")
    
    if not version:
        version = get_package_version(name=name, arch=arch)

    return PackageMetadata(name=name, arch=arch, version=version)
        

def _get_input_package_metadatas() -> Set[PackageMetadata]:
    with open(DEB_PACKAGE_IN, "r") as input_file:
        entries = set(input_file.read().splitlines())
    
    return {_get_package_metadata(entry) for entry in entries if entry and not entry.startswith("#")}
   

def main():
    for package_metadata in _get_input_package_metadatas():
        if package_metadata.name == "dummy":
            print(find_package_in_registry(package_metadata))
        else:
            package = create_deb_package(package_metadata)
            package_dir_name = f"{package.name}_{package.version}_{package.arch}"
            package_dir = MODULES_DIR / package_dir_name
            package_dir.mkdir(parents=True, exist_ok=True)
            write_module_file(package=package, file=package_dir / "MODULE.bazel")
            write_build_file(package=package, file=package_dir / "BUILD.bazel")

if __name__ == "__main__":
    main()