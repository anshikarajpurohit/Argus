"""Bounded asynchronous queues with idempotent retries and exponential backoff."""
import logging
import time
from collections import deque
from threading import Condition, Thread
import requests
class Transport:
    def __init__(self, cfg: dict):
        self.cfg=cfg;self.events=deque(maxlen=5000);self.alerts=deque(maxlen=5000)
        self.cv=Condition();self.stopped=False;self.session=requests.Session()
        self.session.headers['x-agent-key']=cfg['agent_api_key']
        self.worker=Thread(target=self.run,daemon=True);self.worker.start()
    def add(self,event: dict) -> None:
        with self.cv: self.events.append(event);self.cv.notify()
    def alert(self,alert: dict) -> None:
        with self.cv: self.alerts.append(alert);self.cv.notify()
    def settings(self) -> dict | None:
        try:
            response=requests.get(self.cfg['backend_url']+'/api/settings',headers={'x-agent-key':self.cfg['agent_api_key']},timeout=2)
            response.raise_for_status();data=response.json()
            if (data.get('responseMode') in ('suspend','alert_only') and 0<=data['warningThreshold']<data['criticalThreshold']<=100 and isinstance(data['processAllowlist'],list)): return data
        except (requests.RequestException,ValueError,KeyError,TypeError): pass
        return None
    def run(self) -> None:
        next_flush=time.monotonic()+2;retry_at=0;delay=1
        while not self.stopped:
            now=time.monotonic()
            with self.cv:
                if now<retry_at or not (self.alerts or len(self.events)>=200 or (self.events and now>=next_flush)):
                    self.cv.wait(timeout=0.1);continue
                is_alert=bool(self.alerts);batch=list(self.alerts)[:1] if is_alert else list(self.events)[:200]
            try:
                response=self.session.post(self.cfg['backend_url']+('/api/alerts' if is_alert else '/api/events/batch'),json=batch[0] if is_alert else {'events':batch},timeout=3)
                response.raise_for_status()
            except requests.RequestException:
                retry_at=time.monotonic()+delay;delay=min(delay*2,30);continue
            with self.cv:
                queue=self.alerts if is_alert else self.events
                key='alertId' if is_alert else 'eventId';sent={e[key] for e in batch}
                remaining=[e for e in queue if e[key] not in sent];queue.clear();queue.extend(remaining)
            delay=1;retry_at=0
            if not is_alert: next_flush=time.monotonic()+2
    def close(self) -> None:
        self.stopped=True
        with self.cv: self.cv.notify_all()
        self.worker.join(timeout=4)
        if self.events or self.alerts: logging.warning('Shutdown with unsent in-memory records; queues are not durable')
        self.session.close()
