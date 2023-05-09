import sys

from pathlib import Path

import pytest
import unittest

from src.read_input_file import read_input_file
from src.package import PackageMetadata

def test_assertion_when_package_has_no_arch():
    """Input file with entries that don't have architecture, should fail."""
    test_case = unittest.TestCase()
    with test_case.assertRaises(ValueError) as ctx:
        read_input_file(
            registry_path=Path("../resources/registry"), 
            input_file=Path("../_main/tests/resources/faulty_input.in").resolve()
        )
    
    test_case.assertEqual(
        str(ctx.exception), 
        "Entry has unexpected format, expected format: name:arch=version or name:arch"
    )
    
def test_correct_input_file():
    """Tests correct input files."""
    test_case = unittest.TestCase()
    metadatas = read_input_file(            
                    registry_path=Path("../resources/registry"), 
                    input_file=Path("../_main/tests/resources/correct_input.in").resolve()
                )
    
    test_case.assertEqual(len(metadatas), 2)
    test_case.assertTrue(PackageMetadata(name="iproute2", arch="arm64", version="1.2.3") in metadatas)
    
    meta1, meta2 = metadatas
    # one of the entries is patchelf
    test_case.assertTrue(
        meta1.name == "patchelf" or meta2.name == "patchelf"
    )
    # the patchelf entry must have amd64 architecture
    test_case.assertTrue(
        meta1.arch == "amd64" or meta2.arch == "amd64"
    )
    # both entries should have a version
    test_case.assertTrue(
        meta1.version and meta2.version
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
