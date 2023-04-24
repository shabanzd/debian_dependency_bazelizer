from typing import Final, Set
from pathlib import Path

import os

from create_deb_package import create_deb_package
from package import PackageMetadata
from get_package_version import get_package_version
from registry import find_package_in_registry

BAZEL_WORKSPACE_DIR: Final = os.environ["BUILD_WORKSPACE_DIRECTORY"]
DEB_PACKAGE_IN: Final = Path().joinpath(
    BAZEL_WORKSPACE_DIR, "src", "deb_packages.in"
)


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
            print(create_deb_package(package_metadata))

if __name__ == "__main__":
    main()