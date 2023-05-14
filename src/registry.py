"""registry utils."""

from typing import Any, Final, Optional
from pathlib import Path
import json
import os

from src.module import Module, get_module_name, get_module_version
from src.package import Package, PackageMetadata
from src.get_package_version import get_version_from_registry
from src.writers import write_module_file, write_file

BAZEL_WORKSPACE_DIRECTORY_ENV: Final = "BUILD_WORKSPACE_DIRECTORY"
REGISTRY_DIR: Final = Path("registry")
MODULES_DIR: Final = Path("modules")
RPATHS_DOT_TXT: Final = Path("rpaths.txt")
METADATA_DOT_JSON: Final = Path("metadata.json")
SOURCE_DOT_JSON: Final = Path("source.json")
VERSION_DOT_TXT: Final = Path("version.txt")
MODULE_DOT_BAZEL: Final = Path("MODULE.bazel")
BAZEL_REGISTRY_DOT_JSON: Final = Path("bazel_registry.json")

def _get_registry_path() -> Path:
    return Path(os.environ[BAZEL_WORKSPACE_DIRECTORY_ENV]) / REGISTRY_DIR

def _get_module_path_in_registry(module_name: str) -> Path:
    return _get_registry_path() / MODULES_DIR / module_name

def _get_module_version_path_in_registry(module_name: str, module_version: str):
    return _get_module_path_in_registry(module_name) / module_version

def _json_dump(json_file, obj, sort_keys=True):
    with open(file=json_file, mode="w", encoding="utf-8") as file:
        json.dump(obj, file, indent=4, sort_keys=sort_keys)
        file.write("\n")


def find_package_in_registry(
        registry_path: Path,
        package_metadata: PackageMetadata,
) -> Optional[Module]:
    """
    Tries to find package in registry.
    Returns Null if package not found and a Debian Module Object otherwise.
    """
    found_version = get_version_from_registry(
        registry_path=registry_path,
        name=package_metadata.name,
        version_spec=package_metadata.version,
        arch=package_metadata.arch,
    )
    if not found_version:
        return None

    package = Module(
        name=package_metadata.name,
        version=found_version,
        arch=package_metadata.arch,
    )
    with open(
        file=Path(
            _get_module_version_path_in_registry(
                module_name=package.module_name(),
                module_version=package.module_version(),
            ),
            RPATHS_DOT_TXT,
        ),
        mode="r",
        encoding="utf-8",
    ) as file:
        package.rpaths = set(file.read().splitlines())

    return package


def add_package_to_registry(package: Package):
    """Adds modularized package to local registry"""
    module_name = get_module_name(name=package.name, arch=package.arch)
    module_version = get_module_version(package.version)
    module_path_in_registry = _get_module_version_path_in_registry(
        module_name=module_name, module_version=module_version
    )
    module_path_in_registry.mkdir(parents=True, exist_ok=True)

    metadata_path = Path(
        _get_module_path_in_registry(module_name), METADATA_DOT_JSON
    )

    metadata: Any

    if metadata_path.exists():
        metadata = json.load(metadata_path.open(encoding="utf-8"))
        metadata["versions"].append(module_version)
        # TODO(zshaban): sort the list
        metadata["versions"] = list(set(metadata["versions"]))
    else:
        metadata = {
            "versions": [module_version],
        }

    _json_dump(metadata_path, metadata)

    source_json = {
        "type": "local_path",
        "path": f"modules/{package.prefix}/",
    }
    _json_dump(Path.joinpath(module_path_in_registry, SOURCE_DOT_JSON), source_json)

    bazel_registry_json = {
        "module_base_path": "../"
    }
    _json_dump(Path.joinpath(_get_registry_path(), BAZEL_REGISTRY_DOT_JSON), bazel_registry_json)

    write_module_file(package=package, file=Path.joinpath(module_path_in_registry, MODULE_DOT_BAZEL))
    write_file(
        "\n".join([os.fspath(path) for path in package.rpaths]),
        Path.joinpath(module_path_in_registry, RPATHS_DOT_TXT),
    )
    write_file(package.version, Path.joinpath(module_path_in_registry, VERSION_DOT_TXT))
