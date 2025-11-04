import pytest
import sys
from pathlib import Path
from src.bazelize_deps import _add_deps_to_stack
from src.package import Package, PackageMetadata

def test_add_deps_to_stack():
    # Test setup
    package_metadata = PackageMetadata(name="test-package", arch="amd64", version="1.0.0")
    package_stack = []
    visited_modules = set()
    
    # Create a test package with no deps
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
    
    deb_package_cache = {package_metadata: package}
    
    # Test the function
    result = _add_deps_to_stack(package_metadata, package_stack, visited_modules, deb_package_cache)
    assert result == False  # No deps were added

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
