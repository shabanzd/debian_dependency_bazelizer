"""File containing an input file reader for deb packages."""
from typing import List, Set
from pathlib import Path

from src.package import PackageMetadata
from src.get_package_version import get_package_version


def _get_package_metadata(registry_path: Path, pinned_package: str) -> PackageMetadata:
    if pinned_package.count(":") != 1 or pinned_package.count("=") > 1:
        raise ValueError(
            f"Entry {repr(pinned_package)} has unexpected format, expected 'name:arch=version' or 'name:arch'"
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


def read_input_files(
    registry_path: Path, input_files: List[Path]
) -> Set[PackageMetadata]:
    """Reads input files and returns a Set of PackageMetadatas."""
    entries: Set[str] = set()
    for input_file in input_files:
        entries.update(set(input_file.read_text().splitlines()))

    return {
        _get_package_metadata(registry_path=registry_path, pinned_package=entry)
        for entry in entries
        if entry and not entry.startswith("#")
    }
