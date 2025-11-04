import pytest
import sys
from pathlib import Path
from src.package import Package

def test_package_creation():
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
    assert package.name == "test-package"
    assert package.version == "1.0.0"

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
