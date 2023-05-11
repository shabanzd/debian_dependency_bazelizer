from pathlib import Path

import pytest
import sys

from src.read_input_file import read_input_file
from src.package import PackageMetadata

def test_assertion_when_package_has_no_arch():
    """Input file with entries that don't have architecture, should fail."""
    with pytest.raises(ValueError, match="Entry 'iproute2' has unexpected format, expected 'name:arch=version' or 'name:arch'"):
        read_input_file(
            registry_path=Path("../resources/registry"), 
            input_file=Path("../_main/tests/resources/faulty_input.in").resolve()
        )
    
def test_correct_input_file():
    """Tests correct input files."""
    metadatas = read_input_file(            
                    registry_path=Path("../resources/registry"), 
                    input_file=Path("../_main/tests/resources/correct_input.in").resolve()
                )
    
    assert len(metadatas) == 2
    assert PackageMetadata(name="iproute2", arch="arm64", version="1.2.3") in metadatas
    
    meta1, meta2 = metadatas
    # one of the entries is patchelf
    assert meta1.name == "patchelf" or meta2.name == "patchelf"
    
    # the patchelf entry must have amd64 architecture
    assert meta1.arch == "amd64" or meta2.arch == "amd64"
    
    # both entries should have a version
    assert meta1.version and meta2.version


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
