from pathlib import Path
from typing import Final, Dict

import json
import os

from dep_bazelizer_config import get_deb_packages_path, get_storage_config_file_path
from src.bazelize_deps import bazelize_deps
from src.read_input_files import read_input_files

BAZEL_WORKSPACE_DIR: Final = (
    os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    or os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
    or os.environ.get("TEST_TMPDIR")
)
MANDATORY_CONFIGS: Final = ["upload_bucket", "upload_url"]


def _get_storage_config(json_config_file: Path):
    if json_config_file.suffix != ".json":
        path_str = str(json_config_file)
        raise ValueError(f"The file '{path_str}' must be a .json file.")

    with open(json_config_file, encoding="utf-8") as json_config:
        storage_config = json.load(json_config)

    _verify_storage_config(storage_config)

    return storage_config


def _verify_storage_config(configs: Dict[str, str]):
    for mandatory_config in MANDATORY_CONFIGS:
        if mandatory_config not in configs:
            raise ValueError(f"missing mandatory config: {mandatory_config}.")

def main_module():
    """Turns input deb packages into modules referenced by a local registry."""
    registry_path = Path().joinpath(BAZEL_WORKSPACE_DIR, "registry")

    bazelize_deps(
        registry_path=registry_path,
        storage_config=_get_storage_config(Path(get_storage_config_file_path())),
        input_package_metadatas=read_input_files(
            registry_path=registry_path, input_files=[Path(get_deb_packages_path())]
        )
    )


if __name__ == "__main__":
    main_module()
