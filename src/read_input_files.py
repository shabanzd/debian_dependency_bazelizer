"""File containing an input file reader for deb packages."""

from collections import defaultdict
from typing import Dict, Iterable, Set
from pathlib import Path

import functools

from src.package import PackageMetadata
from src.version import (
    get_package_version,
    get_compatibility_level,
    compare_version_strings,
)


def _get_package_metadata(pinned_package: str) -> PackageMetadata:
    _check_entry(pinned_package)
    # entries format: name:arch=version
    name, arch_version = pinned_package.split(":", maxsplit=1)
    version = ""
    arch = arch_version

    if "=" in arch_version:
        arch, version = arch_version.split("=")

    if arch != "amd64":
        raise ValueError(
            f"Unsupported architecture {arch}. Only amd64 arch is supported so far."
        )

    if not version:
        version = get_package_version(name=name, arch=arch)

    return PackageMetadata(name=name, arch=arch, version=version)


def _check_entry(entry: str) -> bool:
    if (
        entry.count(":") == 0
        or entry.count("=") > 1
        or (entry.count(":") > 1 and entry.count("=") == 0)
    ):
        raise ValueError(
            f"Entry {repr(entry)} has unexpected format, expected 'name:arch=version' or 'name:arch'"
        )

    return True


def _get_unique_pacakges(package_versions: Set[str]) -> Set[str]:
    if len(package_versions) == 1:
        return {package_versions.pop()}

    compatible_versions_dict = defaultdict(list)
    package_arch = ""
    for package_version in package_versions:
        if "=" not in package_version:
            continue

        package_arch, version = package_version.split("=")
        compatibility_level = get_compatibility_level(version)

        compatible_versions_dict[compatibility_level].append(version)

    for key, compatible_versions in compatible_versions_dict.items():
        compatible_versions.sort(key=functools.cmp_to_key(compare_version_strings))
        compatible_versions_dict[key] = [compatible_versions[-1]]

    return {
        f"{package_arch}={version[0]}" for version in compatible_versions_dict.values()
    }


def read_input_files(input_files: Iterable[Path]) -> Set[PackageMetadata]:
    """Reads input files and returns a Set of PackageMetadatas."""
    input_packages_dict: Dict[str, Set[str]] = {}
    for input_file in input_files:
        input_packages = input_file.read_text().splitlines()

        for input_package in input_packages:
            if (
                not input_package
                or input_package.startswith("#")
                or not _check_entry(input_package)
            ):
                continue

            package_name_arch = input_package.split("=")[0]
            if package_name_arch not in input_packages_dict:
                input_packages_dict[package_name_arch] = set()

            input_packages_dict[package_name_arch].add(input_package)

    return {
        _get_package_metadata(pinned_package=entry)
        for entries in input_packages_dict.values()
        for entry in _get_unique_pacakges(entries)
    }
