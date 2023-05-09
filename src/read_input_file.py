"""File containing an input file reader for deb packages."""
from typing import Set
from pathlib import Path

from src.package import PackageMetadata
from src.get_package_version import get_package_version

def _get_package_metadata(registry_path: Path, pinned_package: str) -> PackageMetadata:
    if pinned_package.count(":") != 1 or pinned_package.count("=") > 1:
        raise ValueError(
            "Entry has unexpected format, expected format: name:arch=version or name:arch"
        )
    # entries format: name:arch=version
    name, arch_version = pinned_package.split(":")
    version = ""
    arch = arch_version

    if "=" in arch_version:
        arch, version = arch_version.split("=")

    if not version:
        version = get_package_version(registry_path=registry_path, name=name, arch=arch)

    return PackageMetadata(name=name, arch=arch, version=version)

def read_input_file(registry_path: Path, input_file: Path) -> Set[PackageMetadata]:
    """Reads input file and returns a Set of PackageMetadatas."""
    with open(input_file, "r", encoding='utf-8') as file:
        entries = set(file.read().splitlines())

    return {
        _get_package_metadata(registry_path=registry_path, pinned_package=entry)
        for entry in entries if entry and not entry.startswith("#")
    }
   