from typing import Dict, List, Set
import shutil

from modularize_package import modularize_package
from package import Package, PackageMetadata
from create_deb_package import create_deb_package
from module import Module
from registry import find_package_in_registry


def _add_deps_to_stack(
    package_metadata: PackageMetadata,
    package_stack: List[Module],
    visited: Set[PackageMetadata],
    deb_package_cache: Dict[PackageMetadata, Package],
):
    deps_added = False
    for dep_metadata in deb_package_cache[package_metadata].deps:
        if dep_metadata in visited:
            continue

        package_stack.append(dep_metadata)
        deps_added = True

    return deps_added


def _print_summary(deb_package_cache: Dict[str, Package]):
    if not deb_package_cache:
        print("=========================")
        print("No packages were modularized")
        print("=========================")
        return

    package_str = "package was" if len(deb_package_cache) == 1 else "packages were"
    print("=========================")
    print(f"{len(deb_package_cache)} {package_str} modularized:")
    print("=========================")

    i = 0
    for _, package in deb_package_cache.items():
        i += 1
        print(f"{i}) {package.pinned_name}")


def bazelize_deps(input_package_metadatas: Set[PackageMetadata]) -> None:
    visited: Set[PackageMetadata] = set()
    # will be used as a stack for the DFS algorithm
    package_stack: List[PackageMetadata] = []
    deb_package_cache: Dict[PackageMetadata, Package] = dict()

    for input_package_metadata in input_package_metadatas:
        if find_package_in_registry(input_package_metadata):
            visited.add(input_package_metadata)
            continue

        deb_package_cache[input_package_metadata] = create_deb_package(input_package_metadata)

    package_stack = list(deb_package_cache.keys())

    while package_stack:
        if package_stack[-1] in visited:
            package_stack.pop()
            continue

        if find_package_in_registry(package_stack[-1]):
            visited.add(package_stack.pop())
            continue

        if package_stack[-1] not in deb_package_cache:
            deb_package_cache[package_stack[-1]] = create_deb_package(package_stack[-1])

        if not _add_deps_to_stack(
            package_stack[-1],
            package_stack=package_stack,
            deb_package_cache=deb_package_cache,
            visited=visited,
        ):
            package = package_stack.pop()
            modularize_package(deb_package_cache[package])
            visited.add(package)


    _print_summary(deb_package_cache)