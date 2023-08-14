from pathlib import Path
import sys
import pytest
from src.get_storage_config import get_storage_config

def test_get_storage_config_wrong_extension():
    "Test wrong s3 config file extension."
    with pytest.raises(
        ValueError,
        match="The file '../_main/tests/resources/storage_config.txt' must be a .json file.",
    ):
        get_storage_config(Path("../_main/tests/resources/storage_config.txt"))


def test_get_storage_config_missing_url():
    "Test wrong s3 config file - missing mandatory attr: upload_url."
    with pytest.raises(ValueError, match="missing mandatory config: upload_url."):
        get_storage_config(
            Path("../_main/tests/resources/missing_url_storage_config.json")
        )


def test_get_storage_config_missing_config():
    "Test wrong s3 config file - missing mandatory attr: storage."
    with pytest.raises(ValueError, match="missing mandatory config: storage."):
        get_storage_config(
            Path("../_main/tests/resources/missing_storage_storage_config.json")
        )

def test_get_bucket_config_missing_config():
    "Test wrong s3 config file - missing mandatory attr: bucket."
    with pytest.raises(ValueError, match="missing mandatory storage config: bucket."):
        get_storage_config(
            Path("../_main/tests/resources/missing_bucket_storage_config.json")
        )


def test_get_storage_config_correct():
    "Test correct s3 config file."
    config = get_storage_config(
        Path("../_main/tests/resources/correct_storage_config.json")
    )
    assert len(config) == 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
