from pathlib import Path
from typing import Final

import os

from dep_bazelizer_config import get_deb_packages_path, get_storage_config_file_path, get_registry_path_relative_to_root
from src.bazelize_deps import bazelize_deps
from src.read_input_files import read_input_files
from src.storage import create_storage

BAZEL_WORKSPACE_DIR: Final = (
    os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    or os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
    or os.environ.get("TEST_TMPDIR")
)

BAZEL_WORKSPACE_DIR_STR: Final = BAZEL_WORKSPACE_DIR if BAZEL_WORKSPACE_DIR else ""


def main_module():
    """Turns input deb packages into modules referenced by a local registry."""
    registry_path = Path().joinpath(BAZEL_WORKSPACE_DIR_STR, get_registry_path_relative_to_root())

    bazelize_deps(
        registry_path=registry_path,
        storage=create_storage(Path(get_storage_config_file_path())),
        input_package_metadatas=read_input_files(
            registry_path=registry_path, input_files=[Path(get_deb_packages_path())]
        )
    )


if __name__ == "__main__":
    main_module()
