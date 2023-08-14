import pytest
import sys

from click.testing import CliRunner

from src.main import main


def test_main():
    "Test main arguements"
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "-rp" in result.output
    assert "-if" in result.output
    assert "-cf" in result.output

    result = runner.invoke(main)
    assert result.exit_code != 0
    assert "Error: Missing option '--input_file' / '-if'" in result.output

    result = runner.invoke(main, ["-if", "./tests/ci_inputs/deb_packages.in"])
    assert result.exit_code != 0
    assert "Error: Missing option '--storage_config_file' / '-cf'" in result.output


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
