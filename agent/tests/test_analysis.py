import random
from edr_agent.analyzer import Analyzer,entropy,entropy_spike,extension_change
from edr_agent.features import features,FEATURE_NAMES,vector
from edr_agent.window import Window
from edr_agent.scoring import Scorer
from edr_agent.ml_model import Model

def test_entropy_boundaries():
    assert entropy(bytes(5000))==0
    assert entropy(random.Random(42).randbytes(65536))>7.9
    assert 3<entropy(b'The quick brown fox jumps over the lazy dog. '*100)<5.5
    assert entropy(b'')==0

def test_analysis_and_missing_file(tmp_path,cfg):
    p=tmp_path/'a.txt';p.write_bytes(b'hello world '*1000);a=Analyzer(cfg);first=a.event('created',str(p));assert first['prevEntropy'] is None
    p.write_bytes(random.Random(1).randbytes(65536));second=a.event('modified',str(p));assert entropy_spike(second,cfg)
    p.unlink();missing=a.event('modified',str(p));assert missing['entropy'] is None and missing['sizeBytes'] is None
    p.write_bytes(b'small');assert a.event('created',str(p))['entropy'] is None

def test_extension_and_compressed_exemption(tmp_path,cfg):
    p=tmp_path/'a.zip';p.write_bytes(b'a'*5000);a=Analyzer(cfg);a.event('created',str(p));p.write_bytes(random.Random(4).randbytes(8192));assert not entropy_spike(a.event('modified',str(p)),cfg)
    event=a.event('moved',str(tmp_path/'a.txt'),str(tmp_path/'a.locked'));assert extension_change(event,cfg)
    event['destExt']='.md';assert not extension_change(event,cfg)

def test_window_features_scoring_and_dedup(tmp_path,cfg):
    a=Analyzer(cfg);events=[]
    for i in range(25):
        e=a.event('modified',str(tmp_path/f'd{i%6}'/f'f{i}.txt'),ts=100+i/100);e.update(entropy=7.9,prevEntropy=4.2);events.append(e)
    f=features(events,cfg);assert f['n_entropy_spike']==25 and f['n_dirs']==6;assert len(vector(f))==len(FEATURE_NAMES)==12
    window=Window(10)
    for e in events:window.add(e)
    assert len(window.snapshot(105))==25;assert window.snapshot(111)==[]
    scorer=Scorer(cfg);alert=scorer.alert(events,105,cfg);assert alert['severity']=='CRITICAL' and alert['score']==80
    assert scorer.alert(events,106,cfg) is None;assert scorer.alert(events,135,cfg)
    events[0]['isCanary']=True;assert scorer.alert(events,136,cfg,immediate=True)['score']==100

def test_missing_model(tmp_path):
    assert Model(str(tmp_path/'absent.joblib')).probability({}) is None

def test_ml_signal(cfg):
    f=features([],cfg);assert Scorer(cfg).score(f,.81)==(30,['ml_high_probability'])
