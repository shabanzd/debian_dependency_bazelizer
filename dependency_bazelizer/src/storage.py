import abc
import json
import os

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Dict

import boto3

STORAGE: Final = "storage"
UPLOAD_URL: Final = "upload_url"
DOWNLOAD_URL: Final = "download_url"
BUCKET: Final = "bucket"
CREDENTIALS_PROFILE: Final = "credentials_profile"
AWS_S3: Final = "aws_s3"
MANDATORY_CONFIGS: Final = [UPLOAD_URL, STORAGE]
SUPPORTED_STORAGES: Final = [AWS_S3]
MANDATORY_AWS_S3_STORAGE_CONFIGS: Final = [BUCKET]
PREFIX = "dependency_bazelizer"

@dataclass()
class Storage:
    """Storage class."""
    def __init__(self, upload_url: str):
        self.upload_url = upload_url
    
    @abc.abstractmethod
    def upload_file(self, file: Path):
        """Upload file to storage"""
    
    @abc.abstractmethod
    def get_download_url(self, file: Path) -> str:
        """Gets the download endpoint of the file."""

class S3Storage(Storage):
    """AWS S3 storage class."""
    """Config class for aws s3 storages."""
    def __init__(self, aws_s3_specific_configs: Dict[str, str], upload_url: str):
        super().__init__(upload_url=upload_url)
        self._verify_config(aws_s3_specific_configs=aws_s3_specific_configs)
        # mandatory configs
        self.bucket = aws_s3_specific_configs[BUCKET]
        # optional configs
        self.credentials_profile = aws_s3_specific_configs.get(CREDENTIALS_PROFILE, "")
        self.download_url = aws_s3_specific_configs.get(DOWNLOAD_URL, "")

    def _verify_config(self, aws_s3_specific_configs: Dict[str, str]):
        for mandatory_config in MANDATORY_AWS_S3_STORAGE_CONFIGS:
            if mandatory_config not in aws_s3_specific_configs:
                configs_str = ", ".join(aws_s3_specific_configs.keys())
                raise ValueError(
                    f"missing mandatory storage config for aws s3: {mandatory_config}. Found storage configs are: {configs_str}"
                )
    
    def upload_file(self, file: Path):
        client = boto3.client(
            "s3",
            endpoint_url=self.upload_url,
            verify=False,
        )

        file_str = os.fspath(file)
        upload_file_key = PREFIX + "/" + file_str

        client.upload_file(file_str, self.bucket, upload_file_key)
    
    def get_download_url(self, file: Path) -> str:
        """Gets the download endpoint of the file."""
        full_url = f"{self.upload_url}/{self.bucket}/{PREFIX}/{str(file)}"
        if self.download_url:
            full_url = f"{self.download_url}/{PREFIX}/{str(file)}"
        
        return full_url


def create_storage(json_config_file: Path) -> Storage:
    """Function to extract storage configs from json file."""
    if json_config_file.suffix != ".json":
        path_str = str(json_config_file)
        raise ValueError(f"The file '{path_str}' must be a .json file.")

    with open(json_config_file, encoding="utf-8") as json_config:
        configs = json.load(json_config)

    # verify top-level configs
    for mandatory_config in MANDATORY_CONFIGS:
        if mandatory_config not in configs:
            configs_str = ", ".join(configs.keys())
            raise ValueError(
                f"missing mandatory config: {mandatory_config}. Found configs are: {configs_str}"
            )
    
    upload_url = configs[UPLOAD_URL]
    storage_conf = configs[STORAGE]
    if len(storage_conf) > 1:
        raise ValueError("multiple storages are not supported.")
    
    storage = next(iter(storage_conf))
    if storage not in SUPPORTED_STORAGES:
        supported_storages = ",".join(SUPPORTED_STORAGES)
        raise ValueError(
            f"storage: {storage} is not supported. Supported storages are: {supported_storages}."
        )
    
    if storage == AWS_S3:
        return S3Storage(aws_s3_specific_configs=storage_conf[storage], upload_url=upload_url)

    raise ValueError("Could not create Storage object. Storage Config is wrong.")
