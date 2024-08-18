import pytest
import sys

from click.testing import CliRunner

from src.main import main


def test_main():
    "Test main arguements"
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "-i" in result.output
    assert "-m" in result.output

    result = runner.invoke(main)
    assert result.exit_code != 0
    assert "Error: Missing option '--input_file' / '-i'" in result.output

    result = runner.invoke(main, ["-i", "./tests/ci_inputs/deb_packages.in"])
    assert result.exit_code != 0
    assert "Error: Missing option '--modules_path' / '-m'" in result.output


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
