import pytest
import sys

from click.testing import CliRunner
from src.main import main

def test_sync():
  runner = CliRunner()
  result = runner.invoke(main, ["--help"])
  assert result.exit_code == 0
  assert "-mp" in result.output
  assert "-rp" in result.output
  assert "-if" in result.output
  
  result = runner.invoke(main)
  assert result.exit_code != 0
  assert "Error: Missing option '--input_file' / '-if'" in result.output  

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))