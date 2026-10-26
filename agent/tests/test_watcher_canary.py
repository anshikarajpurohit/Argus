import time
import json
from pathlib import Path
from watchdog.events import FileModifiedEvent,FileCreatedEvent,DirModifiedEvent
from edr_agent.watcher import Handler
from edr_agent.canary import Canaries

def test_trailing_debounce_and_ignore(tmp_path,cfg):
    collected=[];handler=Handler(cfg,collected.append)
    for _ in range(5):handler.on_any_event(FileModifiedEvent(str(tmp_path/'a.txt')))
    handler.flush();assert not collected
    time.sleep(.52);handler.flush();assert len(collected)==1
    for path in ['a.tmp','~$doc','repo/.git/config','x/__pycache__/a.pyc']:handler.on_any_event(FileCreatedEvent(str(tmp_path/path)))
    handler.on_any_event(DirModifiedEvent(str(tmp_path)));assert len(collected)==1

def test_canaries_persist_and_recreate(tmp_path,cfg):
    cfg['watch_paths']=[str(tmp_path/'watched')];state=tmp_path/'state/canaries.json';canaries=Canaries(cfg,state)
    assert len(canaries.paths)==3 and len(json.loads(state.read_text()))==3
    before={p:Path(p).stat().st_mtime_ns for p in canaries.paths};Canaries(cfg,state);assert before=={p:Path(p).stat().st_mtime_ns for p in canaries.paths}
    path=next(iter(canaries.paths));Path(path).unlink();canaries.deleted(path);canaries.tick();assert not Path(path).exists()
    canaries.pending[path]=time.monotonic()-1;canaries.tick();assert Path(path).exists()


def test_startup_notifications_do_not_mask_changed_canary(tmp_path,cfg):
    cfg['watch_paths']=[str(tmp_path/'watched')]
    canaries=Canaries(cfg,tmp_path/'state.json');canaries.arm()
    path=next(iter(canaries.paths))
    assert canaries.internal(path,'created')
    assert canaries.internal(path,'modified')
    with Path(path).open('a') as file:file.write('external modification')
    assert not canaries.internal(path,'modified')
    assert not canaries.internal(path,'deleted')
