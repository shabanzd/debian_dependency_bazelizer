from typing import Iterable, Dict, List, Set
from pathlib import Path

from src.package_factory import create_deb_package
from src.module import Module
from src.modularize_package import modularize_package
from src.package import Package, PackageMetadata
from src.registry import find_package_in_registry
from src.storage import Storage


def _add_deps_to_stack(
    package_metadata: PackageMetadata,
    package_stack: List[PackageMetadata],
    visited_modules: Iterable[PackageMetadata],
    deb_package_cache: Dict[PackageMetadata, Package],
):
    deps_added = False
    for dep_metadata in deb_package_cache[package_metadata].deps:
        if dep_metadata in visited_modules:
            continue

        package_stack.append(dep_metadata)
        deps_added = True

    return deps_added


def _print_summary(deb_package_cache: Dict[PackageMetadata, Package]):
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


def bazelize_deps(
    registry_path: Path,
    input_package_metadatas: Set[PackageMetadata],
    storage: Storage,
) -> None:
    """This function bazelizes deps in a topological order."""
    visited_modules: Dict[PackageMetadata, Module] = {}
    # will be used as a stack for the DFS algorithm
    package_stack: List[PackageMetadata] = []
    processed_packages: Dict[PackageMetadata, Package] = {}

    for input_package_metadata in input_package_metadatas:
        module = find_package_in_registry(
            registry_path=registry_path, package_metadata=input_package_metadata
        )
        if module:
            visited_modules[input_package_metadata] = module
            continue

        processed_packages[input_package_metadata] = create_deb_package(
            registry_path=registry_path, metadata=input_package_metadata
        )

    package_stack = list(processed_packages.keys())

    while package_stack:
        if package_stack[-1] in visited_modules:
            package_stack.pop()
            continue

        module = find_package_in_registry(
            registry_path=registry_path, package_metadata=package_stack[-1]
        )
        if module:
            visited_modules[package_stack.pop()] = module
            continue

        if package_stack[-1] not in processed_packages:
            processed_packages[package_stack[-1]] = create_deb_package(
                registry_path=registry_path, metadata=package_stack[-1]
            )

        if not _add_deps_to_stack(
            package_stack[-1],
            package_stack=package_stack,
            deb_package_cache=processed_packages,
            visited_modules=visited_modules,
        ):
            package_metadata = package_stack.pop()
            package = processed_packages[package_metadata]
            modularize_package(
                registry_path=registry_path, package=package, modules=visited_modules, storage=storage
            )
            visited_modules[package_metadata] = Module(
                name=package.name,
                arch=package.arch,
                version=package.version,
                rpaths=package.rpaths,
            )

    _print_summary(processed_packages)
