from typing import Final, Optional
from pathlib import Path
import os

from module import Module
from package import PackageMetadata
from get_package_version import get_version_from_registry

BAZEL_WORKSPACE_DIRECTORY_ENV: Final = "BUILD_WORKSPACE_DIRECTORY"
MODULES_DIR: Final = Path().joinpath("registry", "modules")
RPATHS_DOT_TXT: Final = Path("rpaths.txt")

def _get_src_root_dir():
    return os.environ[BAZEL_WORKSPACE_DIRECTORY_ENV]


def find_package_in_registry(
    package_metadata: PackageMetadata,
) -> Optional[Module]:
    """Tries to find package in registry. Returns Null if package not found and a Debian Module Object otherwise."""
    found_version = get_version_from_registry(
        name=package_metadata.name,
        version=package_metadata.version,
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
        Path(
            _get_src_root_dir(),
            MODULES_DIR,
            package.module_name(),
            package.module_version(),
            RPATHS_DOT_TXT,
        ),
        "r",
    ) as file:
        package.rpaths = set(file.read().splitlines())

    return package