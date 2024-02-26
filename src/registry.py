"""registry utils."""

from typing import Any, Final, Optional
from pathlib import Path
import base64
import hashlib
import json
import subprocess

from src.module import Module, get_module_name, get_module_version
from src.package import Package, PackageMetadata
from src.version import get_version_from_registry
from src.writers import write_module_file, write_file, json_dump

MODULES_DIR: Final = Path("modules")
RPATHS_DOT_JSON: Final = Path("rpaths.json")
METADATA_DOT_JSON: Final = Path("metadata.json")
SOURCE_DOT_JSON: Final = Path("source.json")
VERSION_DOT_TXT: Final = Path("version.txt")
NAME_DOT_TXT: Final = Path("name.txt")
MODULE_DOT_BAZEL: Final = Path("MODULE.bazel")
BAZEL_REGISTRY_DOT_JSON: Final = Path("bazel_registry.json")


def _get_module_path_in_registry(registry_path: Path, module_name: str) -> Path:
    return registry_path / MODULES_DIR / module_name


def _get_module_version_path_in_registry(registry_path: Path, module_name: str, module_version: str):
    return _get_module_path_in_registry(registry_path, module_name) / module_version


def _get_integrity_for_file(debian_module_tar: str):
    files_content = subprocess.check_output(["cat", debian_module_tar])
    hash = hashlib.sha256(files_content).digest()
    hash_base64 = base64.b64encode(hash).decode()
    return f"sha256-{hash_base64}"


def find_module_in_registry(
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
        version_spec="== " + package_metadata.version,
        arch=package_metadata.arch,
    )
    if not found_version:
        return None

    module = Module(
        name=package_metadata.name,
        version=found_version,
        arch=package_metadata.arch,
    )
    rpaths_json_path = _get_module_version_path_in_registry(
            registry_path = registry_path,
            module_name=module.module_name(),
            module_version=module.module_version()
        ) / RPATHS_DOT_JSON
    module.rpaths = json.load(rpaths_json_path.open(encoding="utf-8"))
        
    return module


def add_package_to_registry(registry_path: Path, package: Package, debian_module_tar: str, full_url: str):
    """Adds modularized package to local registry"""
    module_name = get_module_name(name=package.name, arch=package.arch)
    module_version = get_module_version(package.version)
    module_path_in_registry = _get_module_version_path_in_registry(
        registry_path = registry_path, module_name=module_name, module_version=module_version
    )
    module_path_in_registry.mkdir(parents=True, exist_ok=True)

    metadata_path = Path(_get_module_path_in_registry(registry_path, module_name), METADATA_DOT_JSON)

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

    json_dump(metadata_path, metadata)

    source_json = {
        "integrity": _get_integrity_for_file(debian_module_tar),
        "url": full_url,
        "strip_prefix": package.prefix,
    }

    json_dump(Path.joinpath(module_path_in_registry, SOURCE_DOT_JSON), source_json)
    json_dump(Path.joinpath(registry_path, BAZEL_REGISTRY_DOT_JSON), {})
    write_module_file(
        package=package, file=Path.joinpath(module_path_in_registry, MODULE_DOT_BAZEL)
    )
    json_dump(Path.joinpath(module_path_in_registry, RPATHS_DOT_JSON), package.rpaths)
    write_file(package.version, Path.joinpath(module_path_in_registry, VERSION_DOT_TXT))
    write_file(package.name, Path.joinpath(module_path_in_registry, NAME_DOT_TXT))
