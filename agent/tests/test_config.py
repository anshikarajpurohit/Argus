import yaml
import pytest
from edr_agent.config import load_config

def test_config_secret_and_threshold_validation(tmp_path,cfg,monkeypatch):
    monkeypatch.delenv('AGENT_API_KEY',raising=False);p=tmp_path/'config.yaml';p.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):load_config(p)
    monkeypatch.setenv('AGENT_API_KEY','test-key');assert load_config(p)['agent_api_key']=='test-key'
    cfg['warningThreshold']=80;p.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):load_config(p)
