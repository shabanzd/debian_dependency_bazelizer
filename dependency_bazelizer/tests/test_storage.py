from pathlib import Path
import sys
import pytest
from src.storage import create_storage, PREFIX

def test_get_storage_config_wrong_extension():
    "Test wrong s3 config file extension."
    with pytest.raises(
        ValueError,
        match="The file '../_main/tests/resources/storage_config.txt' must be a .json file.",
    ):
        create_storage(Path("../_main/tests/resources/storage_config.txt"))


def test_get_storage_config_missing_url():
    "Test wrong s3 config file - missing mandatory attr: upload_url."
    with pytest.raises(ValueError, match="missing mandatory config: download_url."):
        create_storage(
            Path("../_main/tests/resources/missing_url_storage_config.json")
        )


def test_get_storage_config_missing_config():
    "Test wrong s3 config file - missing mandatory attr: storage."
    with pytest.raises(ValueError, match="missing mandatory config: storage."):
        create_storage(
            Path("../_main/tests/resources/missing_storage_storage_config.json")
        )

def test_get_bucket_config_missing_config():
    "Test wrong s3 config file - missing mandatory attr: bucket."
    with pytest.raises(ValueError, match="missing mandatory storage config for aws s3: bucket. Found storage configs are: credentials_profile"):
        create_storage(
            Path("../_main/tests/resources/missing_bucket_storage_config.json")
        )
    
def test_get_storage_config_correct():
    "Test correct s3 config file."
    storage = create_storage(
        Path("../_main/tests/resources/correct_storage_config.json")
    )
    assert storage.download_url == "https://a13880696afbb75cf78cdb89324aafbc.r2.cloudflarestorage.com"
    assert storage.get_download_url(Path("foo.bar")) == f"https://a13880696afbb75cf78cdb89324aafbc.r2.cloudflarestorage.com/{PREFIX}/foo.bar"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
