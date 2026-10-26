"""Generate reproducible five-minute labeled event streams; no live file mutation."""
import argparse
import csv
import json
import random
import uuid
from pathlib import Path
from common import TESTBED, output_dir
SCENARIOS={'B1':'office_editing','B2':'software_build','B3':'archive_extract','B4':'photo_import','B5':'backup_tool','B6':'idle','B7':'cleanup','M1':'fast_mass_modify','M2':'slow_and_low','M3':'rename_only','M4':'write_then_delete','M5':'canary_first','M6':'mixed_with_benign'}
BASE=1700000000

def stream(kind: str, seed: int, manifest: list[dict]) -> list[dict]:
    rng=random.Random(seed);events=[];texts=[x['path'] for x in manifest if x['label']=='benign_text'];archives=[x['path'] for x in manifest if x['path'].endswith('.zip')]
    def add(t,action='modified',path=None,spike=False,ext=None,canary=False,high=False):
        path=path or rng.choice(texts)
        if ext:path=str(Path(path).with_suffix(ext))
        source='/argus/testbed/'+path; suffix=Path(source).suffix.lower()
        h=min(7.99,max(7.3,rng.gauss(7.8,.1))) if spike or high else min(6.5,max(1,rng.gauss(4.2,.6)))
        previous=rng.gauss(4.2,.3) if spike else h if action=='modified' else None
        dest=source+ rng.choice(['.locked','.enc','.encrypted','.q9x7','.zz1']) if action=='moved' else None
        events.append(dict(eventId=str(uuid.UUID(int=rng.getrandbits(128),version=4)),agentId='agent-001',ts=BASE+min(299.999,max(0,t)),action=action,path=source,destPath=dest,ext=suffix,destExt=Path(dest).suffix if dest else None,sizeBytes=None if action=='deleted' else rng.randint(1024,32768),entropy=None if action=='deleted' else h,prevEntropy=previous,isCanary=canary,suspectPid=None,suspectProcess=None))
    def office():
        t=0
        while t<300:add(t);t+=max(.1,rng.uniform(3,10)+rng.gauss(0,.2))
    def build():
        for start in range(0,300,60):
            n=rng.randint(30,80)
            for i in range(n):add(start+max(0,min(4.99,i*5/n+rng.gauss(0,.025))),rng.choice(['created','modified']),path=f'projects/build/file_{i%18}.py')
    def mass(start=60):
        t=start
        while t<300:
            add(t,spike=True);t+=max(.005,1/rng.uniform(15,40)+rng.gauss(0,.002))
    if kind=='B1':office()
    elif kind=='B2':build()
    elif kind=='B3':
        for start in range(0,300,60):
            n=rng.randint(40,120)
            for i in range(n):add(start+i*10/n,'created',high=i%8==0,ext='.zip' if i%8==0 else None)
    elif kind=='B4':
        for start in range(0,300,60):
            n=rng.randint(30,100)
            for i in range(n):add(start+i*20/n,'created',path=f'photos/image_{i}.jpg',high=True)
    elif kind=='B5':
        for start in range(0,300,60):
            n=rng.randint(100,300)
            for i in range(n):add(start+i*10/n,path=rng.choice(archives),high=True)
    elif kind=='B6':
        for t in range(0,300,30):
            if rng.random()<.5:add(t)
    elif kind=='B7':
        for start in range(0,300,60):
            n=rng.randint(15,40)
            for i in range(n):add(start+i*10/n,'deleted')
    elif kind=='M1':mass()
    elif kind=='M2':
        for t in range(60,300,2):add(t,spike=True)
    elif kind=='M3':
        t=60
        while t<300:add(t,'moved');t+=max(.005,1/rng.uniform(10,30)+rng.gauss(0,.002))
    elif kind=='M4':
        for i in range(2400):
            t=60+i*.099;path=rng.choice(texts);add(t,'created',path=path+'.enc',high=True);add(t+.05,'deleted',path=path)
    elif kind=='M5':add(60,path='_important_passwords.txt',canary=True);mass(65)
    elif kind=='M6':office();build();mass()
    return sorted(events,key=lambda e:e['ts'])

def generate(seed: int=42,runs: int=30) -> None:
    out=output_dir();manifest=json.loads((TESTBED/'MANIFEST.json').read_text());labels=[]
    for index,kind in enumerate(SCENARIOS):
        for run in range(runs):
            name=f'{kind}_{SCENARIOS[kind]}_{run:02}';events=stream(kind,seed+index*1000+run,manifest)
            path=out/(name+'.jsonl')
            if path.is_symlink():raise ValueError('Output stream must not be a symlink')
            path.write_text(''.join(json.dumps(e,separators=(',',':'))+'\n' for e in events))
            labels.append(dict(scenario=name,start_ts=BASE+(60 if kind.startswith('M') else 0),end_ts=BASE+300,label=int(kind.startswith('M'))))
    with (out/'labels.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['scenario','start_ts','end_ts','label']);writer.writeheader();writer.writerows(labels)
    print(f'Generated {len(labels)} streams')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=42);p.add_argument('--runs',type=int,default=30);a=p.parse_args();generate(a.seed,a.runs)
