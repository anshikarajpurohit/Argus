"""Run from repository root: python agent/main.py [--config agent/config.yaml]."""
import argparse
import logging
import queue
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from watchdog.observers import Observer
from edr_agent.config import load_config,ROOT
from edr_agent.analyzer import Analyzer
from edr_agent.canary import Canaries
from edr_agent.features import features
from edr_agent.ml_model import Model
from edr_agent.responder import respond
from edr_agent.scoring import Scorer
from edr_agent.transport import Transport
from edr_agent.watcher import Handler
from edr_agent.window import Window

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'agent/config.yaml');args=parser.parse_args()
    cfg=load_config(args.config);logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    analyzer=Analyzer(cfg);canaries=Canaries(cfg,ROOT/'agent/state/canaries.json')
    raw=queue.Queue(maxsize=5000)
    def enqueue(item):
        try: raw.put_nowait(item)
        except queue.Full:
            try: raw.get_nowait()
            except queue.Empty: pass
            try: raw.put_nowait(item)
            except queue.Full: pass
    handler=Handler(cfg,enqueue)
    for root in cfg['watch_paths']:
        analyzer.baseline([str(p) for p in Path(root).rglob('*') if p.is_file() and not handler.ignored(str(p))])
    transport=Transport(cfg);window=Window(cfg['window_seconds']);scorer=Scorer(cfg);model=Model(cfg['ml_model_path']);settings=cfg.copy()
    observer=Observer()
    for root in cfg['watch_paths']: observer.schedule(handler,root,recursive=True)
    canaries.arm();observer.start();running=True
    def stop(*_):
        nonlocal running
        running=False
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    pool=ThreadPoolExecutor(max_workers=1);future=None;next_settings=0;next_score=time.monotonic()+cfg['score_interval_seconds']
    def send(alert):
        if alert:
            respond(alert,settings);transport.alert(alert);logging.info('Alert %s score=%s reasons=%s',alert['severity'],alert['score'],','.join(alert['reasons']))
    logging.info('Monitoring %s folder(s); response mode %s',len(cfg['watch_paths']),settings['responseMode'])
    try:
        while running:
            handler.flush();canaries.tick();mono=time.monotonic()
            if future and future.done():
                updated=future.result()
                if updated: settings.update(updated)
                future=None
            if mono>=next_settings and future is None: future=pool.submit(transport.settings);next_settings=mono+30
            for _ in range(200):
                try: action,path,dest=raw.get_nowait()
                except queue.Empty: break
                path=str(Path(path).resolve())
                if canaries.internal(path,action): continue
                event=analyzer.event(action,path,dest,path in canaries.paths or (dest is not None and str(Path(dest).resolve()) in canaries.paths))
                transport.add(event);window.add(event)
                if event['isCanary'] and action in ('modified','deleted','moved'):
                    send(scorer.alert([event],time.time(),settings,immediate=True))
                    if action in ('deleted','moved'): canaries.deleted(path)
            if mono>=next_score:
                now=time.time();events=window.snapshot(now);send(scorer.alert(events,now,settings,model.probability(features(events,cfg))));next_score=mono+cfg['score_interval_seconds']
            time.sleep(0.05)
    finally:
        observer.stop();observer.join();transport.close();pool.shutdown(wait=True)
if __name__=='__main__': main()
