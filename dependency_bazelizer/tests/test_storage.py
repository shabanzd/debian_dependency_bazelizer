from pathlib import Path
import sys
import pytest
from src.storage import create_storage, PREFIX

def test_config_wrong_extension():
    "Test wrong s3 config file extension."
    with pytest.raises(
        ValueError,
        match="The file '../_main/tests/resources/storage_config.txt' must be a .json file.",
    ):
        create_storage(Path("../_main/tests/resources/storage_config.txt"))


def test_missing_url_s3_config():
    "Test wrong s3 config file - missing mandatory attr: upload_url."
    with pytest.raises(ValueError, match="missing mandatory config: download_url."):
        create_storage(
            Path("../_main/tests/resources/missing_url_s3_storage_config.json")
        )


def test_missing_storage_s3_config():
    "Test wrong s3 config file - missing mandatory attr: storage."
    with pytest.raises(ValueError, match="missing mandatory config: storage."):
        create_storage(
            Path("../_main/tests/resources/missing_storage_s3_storage_config.json")
        )

def test_missing_bucket_s3_config():
    "Test wrong s3 config file - missing mandatory attr: bucket."
    with pytest.raises(ValueError, match="missing mandatory storage config for aws s3: bucket. Found storage configs are: credentials_profile"):
        create_storage(
            Path("../_main/tests/resources/missing_bucket_s3_storage_config.json")
        )

def test_missing_path_unknown_config():
    "Test wrong unknown storage config file - missing mandatory attr: path."
    with pytest.raises(ValueError, match="missing mandatory storage config for unknown/file storage: path. Found storage configs are: "):
        create_storage(
            Path("../_main/tests/resources/missing_path_unknown_storage_config.json")
        )
    
def test_s3_storage_config_correct():
    "Test correct s3 config file."
    storage = create_storage(
        Path("../_main/tests/resources/correct_s3_storage_config.json")
    )
    assert storage.download_url == "https://testdownloadurl.com"
    assert storage.get_download_url(Path("foo.bar")) == f"https://testdownloadurl.com/{PREFIX}/foo.bar"
    

def test_unknown_storage_config_correct():
    "Test correct unknown storage config file."
    storage = create_storage(
        Path("../_main/tests/resources/correct_unknown_storage_config.json")
    )
    assert storage.download_url == "https://testdownloadurl.com"
    assert storage.get_download_url(Path("foo.bar")) == "https://testdownloadurl.com/foo.bar"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
