"""Best-effort attribution. A matching open handle does not prove authorship."""
import os
from pathlib import Path
import psutil

def attribute(paths: list[str]) -> tuple[int | None,str | None]:
    affected={str(Path(p).resolve()) for p in paths}
    for proc in psutil.process_iter():
        try:
            if any(str(Path(f.path).resolve()) in affected for f in proc.open_files()): return proc.pid,proc.name()
        except (psutil.Error,OSError): continue
    return None,None

def respond(alert: dict, settings: dict) -> None:
    if alert['severity']!='CRITICAL': return
    pid,name=attribute(alert['affectedFiles'])
    alert['suspectPid'],alert['suspectProcess']=pid,name
    protected={0,1,4,os.getpid(),os.getppid()}
    allowed={n.casefold() for n in settings['processAllowlist']}
    if settings['responseMode']!='suspend' or pid is None or pid in protected or (name or '').casefold() in allowed: return
    try:
        proc=psutil.Process(pid)
        # Recheck the name immediately before acting, reducing PID-reuse risk.
        if proc.name()!=name or proc.name().casefold() in allowed: return
        proc.suspend(); alert['responseTaken']='suspended'
    except (psutil.Error,OSError): alert['responseTaken']='suspend_failed'
