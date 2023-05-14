import pytest
import sys
from pathlib import Path
from src.get_package_version import _extract_attribute, get_version_from_registry

class MockFileSystem:
    def __init__(self, exists=True, directories=None, file_content=None):
        self.exists = exists
        self.directories = directories if directories is not None else []
        self.file_content = file_content if file_content is not None else ""
    
    def path_exists(self, path):
        return self.exists
    
    def get_directories(self, path):
        return self.directories
    
    def get_file_contents(self, path):
        return self.file_content

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

def test_get_version_from_registry():
    registry_path = Path('/test/path')
    name = 'test_package'
    arch = 'test_arch'
    version_spec = '>=2.0.0'
    fs = MockFileSystem(exists=True, directories=['1.0.0', '2.0.0', '3.0.0'], file_content='3.0.0')
    version = get_version_from_registry(registry_path, name, arch, version_spec, fs)

    assert version == '3.0.0', "Expected highest version that matches >=2.0.0"

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))