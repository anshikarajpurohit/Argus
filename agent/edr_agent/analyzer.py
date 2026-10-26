"""Bounded byte entropy and best-effort metadata enrichment."""
import math
import time
import uuid
from collections import Counter
from pathlib import Path

def entropy(data: bytes) -> float:
    if not data: return 0.0
    return -sum((n/len(data))*math.log2(n/len(data)) for n in Counter(data).values())

def entropy_spike(event: dict, cfg: dict) -> bool:
    h, previous = event['entropy'], event['prevEntropy']
    return (h is not None and previous is not None and h >= cfg['entropy_spike_min']
            and h-previous >= cfg['entropy_spike_delta'] and event['ext'] not in cfg['high_entropy_ok_ext'])

def extension_change(event: dict, cfg: dict) -> bool:
    return event['action'] == 'moved' and ((event['destExt'] != event['ext'] and event['destExt'] not in cfg['known_ext']) or event['destExt'] in cfg['suspicious_ext'])

class Analyzer:
    def __init__(self, cfg: dict):
        self.cfg, self.cache = cfg, {}

    def event(self, action: str, path: str, dest: str | None = None, canary: bool = False, ts: float | None = None) -> dict:
        path = str(Path(path).resolve())
        dest = str(Path(dest).resolve()) if dest else None
        previous = self.cache.get(path)
        size = h = None
        if action != 'deleted':
            try:
                target = Path(dest or path)
                size = target.stat().st_size
                if size >= self.cfg['entropy_min_file_bytes']:
                    with target.open('rb') as handle: h = entropy(handle.read(self.cfg['entropy_sample_bytes']))
            except OSError:
                size = h = None
        if action in ('deleted','moved'): self.cache.pop(path,None)
        if h is not None: self.cache[dest or path] = h
        return dict(eventId=str(uuid.uuid4()),agentId=self.cfg['agent_id'],ts=ts if ts is not None else time.time(),action=action,path=path,destPath=dest,ext=Path(path).suffix.lower(),destExt=Path(dest).suffix.lower() if dest else None,sizeBytes=size,entropy=h,prevEntropy=previous,isCanary=canary,suspectPid=None,suspectProcess=None)

    def baseline(self, paths: list[str]) -> None:
        for path in paths:
            self.event('created',path)
