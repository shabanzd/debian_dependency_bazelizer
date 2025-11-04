import pytest
import sys
from pathlib import Path
from src.writers import _create_filegroup_content
from src.package import Package

def test_filegroup_content_creation():
    package = Package(
        name="test-package",
        version="1.0.0",
        arch="amd64",
        module_name="test_package_amd64",
        pinned_name="test-package@1.0.0",
        prefix="",
        prefix_version="",
        compatibility_level=0,
        package_dir=Path("."),
        deps=set(),
        files=set(),
        elf_files=set(),
        rpaths={},
        tags=set(),
        detached_mode_metadata=None
    )
    # This should pass as the package has amd64 arch
    _create_filegroup_content(package)
    
    # Test with non-amd64 arch
    package_arm = Package(
        name="test-package",
        version="1.0.0",
        arch="arm64",
        module_name="test_package_arm64",
        pinned_name="test-package@1.0.0",
        prefix="",
        prefix_version="",
        compatibility_level=0,
        package_dir=Path("."),
        deps=set(),
        files=set(),
        elf_files=set(),
        rpaths={},
        tags=set(),
        detached_mode_metadata=None
    )
    # Should raise ValueError for non-amd64 arch
    with pytest.raises(ValueError, match="Only amd64 architecture is supported for now"):
        _create_filegroup_content(package_arm)

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
