from pathlib import Path
import pytest
import yaml
@pytest.fixture
def cfg():
    return yaml.safe_load((Path(__file__).resolve().parents[1]/'config.yaml').read_text())
