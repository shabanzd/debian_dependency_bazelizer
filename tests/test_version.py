from pathlib import Path
from typing import List

import pytest
import pytest_mock
import sys

from src.version import _extract_attribute, get_version_from_registry

def _mock_away_versions_and_file_content(mocker: pytest_mock.MockerFixture, versions: List[str], content: str):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("src.version._get_versions", return_value=versions)
    mocker.patch("src.version._get_file_contents", return_value=content)


def test_extract_attribute_positive():
    package_info = "Attribute: 7.2.3\nAttribute: 2.3.4\nAttribute: 3.4.5"
    attribute = "Attribute"
    result = _extract_attribute(package_info, attribute)

    assert result == "7.2.3", "Expected the highest version to be returned"

def test_extract_attribute_negative():
    package_info = "Attribute: 1.2.3\nAttribute: 2.3.4\nAttribute: 3.4.5"
    attribute = "NonExistingAttribute"
    with pytest.raises(ValueError):
        _extract_attribute(package_info, attribute)

def test_extract_attribute_not_must_exist():
    package_info = "Attribute: 1.2.3\nAttribute: 2.3.4\nAttribute: 3.4.5"
    attribute = "NonExistingAttribute"
    result = _extract_attribute(package_info, attribute, must_exist=False)

    assert result == "", "Expected an empty string when attribute does not exist and must_exist is set to False"

def test_get_version_from_registry_no_versions_matching_spec(mocker: pytest_mock.MockerFixture):
    _mock_away_versions_and_file_content(mocker, ["1.0.0-1", "2.0.0-1ubuntu", "3.0.0"], "3.0.0")
    version = get_version_from_registry(registry_path=Path("/test/path"), name="test_package", arch="test_arch", version_spec=">=5.0.0")

    assert version == "", "Expected no version since none match >=5.0.0"

def test_get_version_from_registry_with_epoch(mocker: pytest_mock.MockerFixture):
    _mock_away_versions_and_file_content(mocker, ["1.0.0-1", "2.0.0-1ubuntu", "3.0.0", "1:2.0.0"], "1:2.0.0")
    version = get_version_from_registry(registry_path=Path("/test/path"), name="test_package", arch="test_arch", version_spec=">=2.0.0")

    assert version == "1:2.0.0", "Expected version with epoch"

def test_get_version_from_registry_with_ubuntu_revision(mocker: pytest_mock.MockerFixture):
    _mock_away_versions_and_file_content(mocker, ["1.0.0-1", "2.0.0-1ubuntu1", "3.0.0", "1:2.0.0"], "2.0.0-1ubuntu1")
    version = get_version_from_registry(registry_path=Path("/test/path"), name="test_package", arch="test_arch", version_spec=">=2.0.0")

    assert version == "2.0.0-1ubuntu1", "Expected version with Ubuntu revision"

def test_get_version_from_registry_with_ubuntu_revision_and_epoch(mocker: pytest_mock.MockerFixture):
    _mock_away_versions_and_file_content(mocker, ["1.0.0-1", "2.0.0-1ubuntu1", "3.0.0", "1:2.0.0"], "1:2.0.0-1ubuntu1")
    version = get_version_from_registry(registry_path=Path("/test/path"), name="test_package", arch="test_arch", version_spec=">=2.0.0")

    assert version == "1:2.0.0", "Expected version with Ubuntu revision"

def test_get_version_from_registry_with_multiple_versions_matching_spec(mocker: pytest_mock.MockerFixture):
    _mock_away_versions_and_file_content(mocker, ["3.0.0", "1.0.0-1", "2.0.0-1ubuntu1", "4.0.0"], "4.0.0")
    version = get_version_from_registry(registry_path=Path("/test/path"), name="test_package", arch="test_arch", version_spec=">=2.0.0")

    assert version == "4.0.0", "Expected highest version that matches >=2.0.0"

def test_get_version_from_registry_with_complex_version_spec(mocker: pytest_mock.MockerFixture):
    _mock_away_versions_and_file_content(mocker, ["2.0.0-1ubuntu1", "1.0.0-1", "3.0.0", "4.0.0"], "3.0.0")
    version = get_version_from_registry(registry_path=Path("/test/path"), name="test_package", arch="test_arch", version_spec= ">=2.0.0,!=4.0.0")

    assert version == "3.0.0", "Expected highest version that matches >=2.0.0 and !=4.0.0"

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
