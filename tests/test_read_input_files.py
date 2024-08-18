from pathlib import Path

import pytest
import sys

from src.read_input_files import read_input_files
from src.package import PackageMetadata

def test_assertion_when_package_has_no_arch():
    """Input file with entries that don't have architecture, should fail."""
    with pytest.raises(ValueError, match="Entry 'iproute2' has unexpected format, expected 'name:arch=version' or 'name:arch'"):
        read_input_files(
            registry_path=Path("../resources/registry"),
            input_files=[Path("../_main/tests/resources/faulty_input.in").resolve()]
        )

def test_correct_input_file():
    """Tests correct input files."""
    metadatas = read_input_files(
                    registry_path=Path("../resources/registry"),
                    input_files=[Path("../_main/tests/resources/correct_input.in").resolve()]
                )
    assert len(metadatas) == 3
    assert PackageMetadata(name="iproute2", arch="amd64", version="1:1.2.4") in metadatas
    assert PackageMetadata(name="patchelf", arch="amd64", version="4.5.6") in metadatas
    assert PackageMetadata(name="patchelf", arch="amd64", version="5.6.7") in metadatas

def test_duplicate_input_files():
    """Tests duplicate input files."""
    metadatas = read_input_files(
                    registry_path=Path("../resources/registry"),
                    input_files=[
                                Path("../_main/tests/resources/correct_input.in").resolve(),
                                Path("../_main/tests/resources/correct_input.in").resolve()
                                ]
                )
    assert len(metadatas) == 3
    assert PackageMetadata(name="iproute2", arch="amd64", version="1:1.2.4") in metadatas
    assert PackageMetadata(name="patchelf", arch="amd64", version="4.5.6") in metadatas
    assert PackageMetadata(name="patchelf", arch="amd64", version="5.6.7") in metadatas

def test_arm_input_files():
    """Tests arm input files."""
    with pytest.raises(ValueError) as e:
        read_input_files(
                    registry_path=Path("../resources/registry"),
                    input_files=[
                                Path("../_main/tests/resources/arm_input.in").resolve(),
                                ]
                )
    assert str(e.value) == "Unsupported architecture arm64. Only amd64 arch is supported so far."

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
