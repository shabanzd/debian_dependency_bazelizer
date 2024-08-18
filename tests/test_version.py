import pytest
import sys

from src.version import _extract_attribute


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

    assert (
        result == ""
    ), "Expected an empty string when attribute does not exist and must_exist is set to False"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
