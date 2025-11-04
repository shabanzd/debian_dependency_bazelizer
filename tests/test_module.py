import pytest
import sys
from src.module import get_module_name


def test_module_creation():
    # Test the get_module_name function
    module_name = get_module_name("test-package", "amd64")
    assert module_name == "test_package_amd64"

    # Test with a package starting with a number
    module_name = get_module_name("2test-package", "amd64")
    assert module_name == "package_2test_package_amd64"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
