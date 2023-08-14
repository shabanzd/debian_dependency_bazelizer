import json

from pathlib import Path
from typing import Any, Final, Dict

STORAGE: Final = "storage"
MANDATORY_CONFIGS: Final = ["upload_url", "storage"]
MANDATORY_STORAGE_CONFIGS: Final = {
    "aws_s3": ["bucket"],
}


def _verify_storage_config(configs: Dict[str, Any]):
    for mandatory_config in MANDATORY_CONFIGS:
        if mandatory_config not in configs:
            configs_str = ", ".join(configs)
            raise ValueError(
                f"missing mandatory config: {mandatory_config}. Found configs are: {configs_str}"
            )

    storage_conf = configs[STORAGE]
    if len(storage_conf) > 1:
        raise ValueError("multiple storages are not supported.")

    storage = next(iter(storage_conf))
    if storage not in MANDATORY_STORAGE_CONFIGS:
        supported_storages = ",".join(MANDATORY_STORAGE_CONFIGS.keys())
        raise ValueError(
            f"storage: {storage} is not supported. Supported storages are: {supported_storages}."
        )

    for mandatory_config in MANDATORY_STORAGE_CONFIGS[storage]:
        if mandatory_config not in storage_conf[storage]:
            configs_str = ", ".join(configs)
            raise ValueError(
                f"missing mandatory storage config: {mandatory_config}. Found storage configs are: {configs_str}"
            )


def get_storage_config(json_config_file: Path):
    """Function to extract storage configs from json file."""
    if json_config_file.suffix != ".json":
        path_str = str(json_config_file)
        raise ValueError(f"The file '{path_str}' must be a .json file.")

    with open(json_config_file, encoding="utf-8") as json_config:
        storage_config = json.load(json_config)

    _verify_storage_config(storage_config)

    return storage_config
