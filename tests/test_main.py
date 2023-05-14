import pytest
import sys

from click.testing import CliRunner
from pathlib import Path
from src.main import main, _get_s3_config

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
  assert "Error: Missing option '--s3_config_file' / '-cf'" in result.output
  
def test_get_s3_config_wrong_extension():
  "Test wrong s3 config file extension."
  with pytest.raises(ValueError, match="The file '../_main/tests/resources/s3_config.txt' must be a .json file."):
    _get_s3_config(Path("../_main/tests/resources/s3_config.txt"))

def test_get_s3_config_missing_url():
  "Test wrong s3 config file - missing mandatory attr: upload_url."
  with pytest.raises(ValueError, match="missing mandatory config: upload_url."):
    _get_s3_config(Path("../_main/tests/resources/missing_url_s3_config.json"))

def test_get_s3_config_missing_url():
  "Test wrong s3 config file - missing mandatory attr: upload_bucket."
  with pytest.raises(ValueError, match="missing mandatory config: upload_bucket."):
    _get_s3_config(Path("../_main/tests/resources/missing_bucket_s3_config.json"))

def test_get_s3_config_missing_url():
  "Test correct s3 config file."
  config = _get_s3_config(Path("../_main/tests/resources/correct_s3_config.json"))
  assert len(config) == 2

if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))